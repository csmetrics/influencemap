"""Lightweight OpenAlex API usage logger.

Every call made through ``core.search.query_info._get`` is appended as a JSON
line to ``logs/openalex_api.jsonl`` (configurable via ``OPENALEX_LOG_PATH``).
Set ``OPENALEX_LOG_DISABLE=1`` to turn logging off.

Run ``python -m core.search.api_logger`` for a daily usage summary against
OpenAlex's free-tier quotas (https://developers.openalex.org/guides/authentication).
"""

import json
import os
import pathlib
import threading
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse


_LOCK = threading.Lock()

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
_DEFAULT_LOG_PATH = _PROJECT_ROOT / 'logs' / 'openalex_api.jsonl'

# Free-tier daily caps from OpenAlex authentication docs.
QUOTAS = {
    'single': None,          # unlimited
    'list':   10_000,        # list + filter
    'search': 1_000,         # full-text search
}


def _log_path():
    p = os.environ.get('OPENALEX_LOG_PATH')
    return pathlib.Path(p) if p else _DEFAULT_LOG_PATH


def _logging_enabled():
    return os.environ.get('OPENALEX_LOG_DISABLE', '') not in ('1', 'true', 'True')


def classify(url, params):
    """Classify an OpenAlex call as 'single', 'search', or 'list'.

    - 'single' : ``/{entity_type}/{PrefixID}`` path with no query params that
                 imply listing (single-entity lookup, unlimited under free tier).
    - 'search' : has a ``search=`` param, or a ``filter`` containing
                 ``.search:`` (full-text search; capped at 1k/day).
    - 'list'   : every other ``/{entity_type}`` call (list + filter; 10k/day).
    """
    path_parts = [s for s in urlparse(url).path.split('/') if s]
    if len(path_parts) >= 2:
        last = path_parts[-1]
        if last[:1].isalpha() and last[1:].isdigit():
            return 'single'

    p = params or {}
    if 'search' in p:
        return 'search'
    filt = p.get('filter')
    if filt and '.search:' in str(filt):
        return 'search'
    return 'list'


def log_call(*, url, params, response, latency_ms, error=None):
    """Append one record to the log file. Never raises."""
    if not _logging_enabled():
        return
    try:
        category = classify(url, params)
        entry = {
            'ts': datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
            'url': url.split('?', 1)[0],
            'category': category,
            'param_keys': sorted((params or {}).keys()),
            'latency_ms': round(latency_ms, 1),
        }
        if response is not None:
            entry['status'] = response.status_code
            try:
                body = response.json()
            except Exception:
                body = None
            if isinstance(body, dict):
                meta = body.get('meta') or {}
                if 'count' in meta:
                    entry['meta_count'] = meta.get('count')
                results = body.get('results')
                if isinstance(results, list):
                    entry['results_returned'] = len(results)
                elif body.get('id'):
                    entry['results_returned'] = 1
                # Capture error payload on non-2xx (e.g. 429 limit-exceeded
                # message from OpenAlex). Truncate so a runaway body cannot
                # blow up the log file.
                if not (200 <= response.status_code < 300):
                    err_msg = body.get('error') or body.get('message')
                    if err_msg:
                        entry['error_body'] = str(err_msg)[:500]
                    else:
                        entry['error_body'] = json.dumps(body)[:500]
            elif not (200 <= response.status_code < 300):
                # Body wasn't JSON; capture raw text (truncated).
                try:
                    entry['error_body'] = response.text[:500]
                except Exception:
                    pass
            for k, v in response.headers.items():
                kl = k.lower()
                if kl.startswith('x-'):
                    entry[f'hdr_{kl}'] = v
        if error is not None:
            entry['error'] = repr(error)

        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False) + '\n'
        with _LOCK:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(line)
    except Exception as e:
        # Logging must never break the calling code.
        print(f"[api_logger] failed to log call: {e!r}")


def _iter_log(path, date_prefix=None):
    if not path.exists():
        return
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if date_prefix and not rec.get('ts', '').startswith(date_prefix):
                continue
            yield rec


def _as_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _duration(start_ts, end_ts):
    """Human-readable diff between two ISO timestamps, or '' if invalid."""
    if not (start_ts and end_ts):
        return ''
    try:
        a = datetime.fromisoformat(start_ts)
        b = datetime.fromisoformat(end_ts)
    except ValueError:
        return ''
    secs = int((b - a).total_seconds())
    if secs < 0:
        return ''
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def summarize(date_str=None, tail=0):
    from collections import Counter
    path = _log_path()
    if not path.exists():
        print(f"No log file at {path}")
        return

    label = date_str or 'all time'
    ok_calls = Counter()        # successful (2xx) calls per category
    rejected_calls = Counter()  # 429 / 403 etc. per category
    results = Counter()
    cost_usd = {}            # category -> sum of x-ratelimit-cost-usd
    latency_sum = {}
    statuses = Counter()
    net_errors = 0           # network/request exceptions (no response)
    rejected_records = []    # for showing example 429 bodies
    last_records = []
    last_remaining_usd = None
    last_remaining_calls = None
    last_reset_seconds = None
    first_call_ts = None
    last_ok_ts = None
    first_rejection_ts = None
    last_rejection_ts = None

    for rec in _iter_log(path, date_prefix=date_str):
        cat = rec.get('category', 'unknown')
        status = rec.get('status')
        ts = rec.get('ts')
        results[cat] += rec.get('results_returned') or 0
        latency_sum.setdefault(cat, []).append(rec.get('latency_ms') or 0)
        statuses[str(status)] += 1

        if first_call_ts is None:
            first_call_ts = ts

        if status is None:
            net_errors += 1
        elif 200 <= int(status) < 300:
            ok_calls[cat] += 1
            last_ok_ts = ts
        else:
            rejected_calls[cat] += 1
            rejected_records.append(rec)
            if first_rejection_ts is None:
                first_rejection_ts = ts
            last_rejection_ts = ts

        cost = _as_float(rec.get('hdr_x-ratelimit-cost-usd'))
        if cost is not None:
            cost_usd[cat] = cost_usd.get(cat, 0.0) + cost
        rem_usd = _as_float(rec.get('hdr_x-ratelimit-remaining-usd'))
        if rem_usd is not None:
            last_remaining_usd = rem_usd
        rem_calls = _as_float(rec.get('hdr_x-ratelimit-remaining'))
        if rem_calls is not None:
            last_remaining_calls = rem_calls
        reset = _as_float(rec.get('hdr_x-ratelimit-reset'))
        if reset is not None:
            last_reset_seconds = reset
        last_records.append(rec)

    total_ok = sum(ok_calls.values())
    total_rejected = sum(rejected_calls.values())
    total_cost = sum(cost_usd.values())

    print(f"=== OpenAlex API usage — {label} ===")
    print(f"Log: {path}")
    print(f"Total calls: ok={total_ok}  rejected={total_rejected}  "
          f"network_errors={net_errors}  "
          f"cost (per headers)=${total_cost:.4f}")
    if last_remaining_usd is not None:
        reset_hint = ''
        if last_reset_seconds is not None:
            hrs, rem = divmod(int(last_reset_seconds), 3600)
            mins, _ = divmod(rem, 60)
            reset_hint = f"  (resets in ~{hrs}h{mins:02d}m)"
        print(f"Last seen remaining today: ${last_remaining_usd:.4f} / $1.00, "
              f"{int(last_remaining_calls) if last_remaining_calls is not None else '?'} calls{reset_hint}")

    if total_rejected:
        print()
        reject_pct = 100 * total_rejected / (total_ok + total_rejected)
        print(f"  ⚠ {total_rejected} call(s) rejected ({reject_pct:.1f}% of {total_ok + total_rejected} total)")
        # Time-to-exhaust and rejection window
        time_to_exhaust = _duration(first_call_ts, first_rejection_ts)
        if time_to_exhaust:
            print(f"    Time to exhaust limit: {time_to_exhaust}  "
                  f"({first_call_ts}  →  {first_rejection_ts})")
        if last_ok_ts and first_rejection_ts:
            gap = _duration(last_ok_ts, first_rejection_ts)
            if gap:
                print(f"    Last successful call: {last_ok_ts}  "
                      f"(gap to first rejection: {gap})")
        if last_rejection_ts and last_rejection_ts != first_rejection_ts:
            window = _duration(first_rejection_ts, last_rejection_ts)
            print(f"    Rejection window:      {window}  "
                  f"({first_rejection_ts}  →  {last_rejection_ts})")
        # Status-code breakdown for rejected
        rejected_statuses = Counter(
            str(r.get('status')) for r in rejected_records)
        print(f"    Rejected by status:   {dict(rejected_statuses)}")
        print(f"    Rejected by category: {dict(rejected_calls)}")
        # Show one sample body so user can see OpenAlex's exact message
        sample = next((r for r in rejected_records if r.get('error_body')), None)
        if sample:
            print(f"    Example body ({sample.get('status')} @ {sample.get('ts')}):")
            print(f"      {sample.get('error_body')}")

    print()
    print(f"  {'category':<8} {'ok':>6} {'reject':>7} {'results':>10} "
          f"{'cost_usd':>10} {'avg_ms':>8} {'quota':>10} {'used %':>8}")
    for cat in ('single', 'list', 'search'):
        n_ok = ok_calls[cat]
        n_rej = rejected_calls[cat]
        r = results[cat]
        c = cost_usd.get(cat, 0.0)
        lats = latency_sum.get(cat) or [0]
        avg = sum(lats) / len(lats) if lats else 0
        q = QUOTAS.get(cat)
        q_str = f"{q:,}" if q else '∞'
        pct = f"{100 * n_ok / q:6.2f}%" if q else '    n/a'
        print(f"  {cat:<8} {n_ok:>6d} {n_rej:>7d} {r:>10d} "
              f"{c:>10.4f} {avg:>8.1f} {q_str:>10} {pct:>8}")
    print()
    print("  Status codes:", dict(statuses))

    if tail:
        print()
        print(f"  Last {tail} calls:")
        for rec in last_records[-tail:]:
            extra = ''
            if rec.get('error_body'):
                extra = f"  body={rec.get('error_body')[:80]!r}"
            print(f"    {rec.get('ts')}  {rec.get('category'):<6}  "
                  f"{rec.get('status')}  {rec.get('latency_ms'):>6}ms  "
                  f"{rec.get('url')}  keys={rec.get('param_keys')}{extra}")


def _today_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Summarize OpenAlex API usage from the local log file.")
    parser.add_argument('--date', help="YYYY-MM-DD (UTC). Default: today.")
    parser.add_argument('--all', action='store_true',
                        help="Aggregate the whole log file, ignoring date.")
    parser.add_argument('--yesterday', action='store_true',
                        help="Summarize yesterday (UTC).")
    parser.add_argument('--tail', type=int, default=0,
                        help="Also print the last N call entries.")
    args = parser.parse_args()

    if args.all:
        date_str = None
    elif args.yesterday:
        date_str = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        date_str = args.date or _today_utc()

    summarize(date_str=date_str, tail=args.tail)


if __name__ == '__main__':
    main()
