"""Smoke-test the Phase 6 swap on the deploy server.

Run this against a live konigsberg (and optionally the webapp). It hits the
two new endpoints directly and verifies their shapes, then exercises an
end-to-end flower render to confirm the webapp gets names from konigsberg
rather than OpenAlex.

Usage:

    # Default: konigsberg at http://localhost:8081
    python -m scripts.smoke_test_phase6

    # Custom URLs and known IDs (override defaults with real-data values)
    KONIGSBERG_URL=http://localhost:8002 \\
    WEBAPP_URL=http://localhost:8001 \\
    AUTHOR_ID=2283863768 \\
    PAPER_ID=2741809807 \\
    python -m scripts.smoke_test_phase6
"""
import json
import os
import sys
import urllib.parse
import urllib.request


KB = os.environ.get('KONIGSBERG_URL', 'http://localhost:8081')
WEBAPP = os.environ.get('WEBAPP_URL', '')  # Empty -> skip webapp checks.

# OpenAlex numeric ids (no prefix letter). Override per environment.
AUTHOR_ID = int(os.environ.get('AUTHOR_ID', '2283863768'))
INSTITUTION_ID = int(os.environ.get('INSTITUTION_ID', '161318765'))
SOURCE_ID = int(os.environ.get('SOURCE_ID', '4306400886'))
CONCEPT_ID = int(os.environ.get('CONCEPT_ID', '41008148'))
PAPER_ID = int(os.environ.get('PAPER_ID', '2741809807'))


PASS = '\x1b[32m✓\x1b[0m'
FAIL = '\x1b[31m✗\x1b[0m'
SKIP = '\x1b[33m·\x1b[0m'


def _get(url, params):
    full = url + '?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=10) as r:
        return r.status, json.loads(r.read())


def check_get_names():
    print('\n[/get-names]')
    cases = [
        ('authors', AUTHOR_ID),
        ('institutions', INSTITUTION_ID),
        ('sources', SOURCE_ID),
        ('concepts', CONCEPT_ID),
    ]
    ok = True
    for etype, eid in cases:
        try:
            status, body = _get(
                KB + '/get-names', {'type': etype, 'ids': str(eid)})
        except Exception as e:
            print(f'  {FAIL} {etype}({eid}): request failed: {e}')
            ok = False
            continue
        name = body.get(str(eid))
        if status == 200 and name:
            preview = name[:60] + ('…' if len(name) > 60 else '')
            print(f'  {PASS} {etype}({eid}) -> "{preview}"')
        else:
            print(f'  {FAIL} {etype}({eid}): status={status} body={body!r}')
            ok = False
    return ok


def check_get_paper_info():
    print('\n[/get-paper-info]')
    try:
        status, body = _get(
            KB + '/get-paper-info', {'ids': str(PAPER_ID)})
    except Exception as e:
        print(f'  {FAIL} request failed: {e}')
        return False
    rec = body.get(str(PAPER_ID))
    if status != 200 or rec is None:
        print(f'  {FAIL} status={status} body={body!r}')
        return False
    missing = [k for k in ('title', 'year', 'venue') if k not in rec]
    if missing:
        print(f'  {FAIL} missing keys in response: {missing}')
        return False
    print(f'  {PASS} paper({PAPER_ID}):')
    print(f'      title: {rec["title"][:80]!r}')
    print(f'      year:  {rec["year"]}')
    print(f'      venue: {rec["venue"][:60]!r}')
    if not rec['title']:
        print(f'  {SKIP} title is empty — paper-title-*.bin may not be loaded')
    return True


def check_batch():
    """Single round-trip with mixed valid+invalid ids; check unknowns drop."""
    print('\n[batch + unknown id handling]')
    try:
        status, body = _get(
            KB + '/get-names',
            {'type': 'authors', 'ids': f'{AUTHOR_ID},999999999999999'})
    except Exception as e:
        print(f'  {FAIL} request failed: {e}')
        return False
    if str(AUTHOR_ID) not in body:
        print(f'  {FAIL} valid id {AUTHOR_ID} missing from response')
        return False
    if '999999999999999' in body:
        print(f'  {FAIL} unknown id leaked into response')
        return False
    print(f'  {PASS} valid id present, unknown id silently dropped')
    return True


def check_webapp_submit():
    """End-to-end: have the webapp render a flower and confirm no API need."""
    if not WEBAPP:
        print(f'\n{SKIP} [webapp]: set WEBAPP_URL=http://... to enable')
        return None
    print('\n[webapp /submit/]')
    # Construct a minimal POST exactly like the production frontend.
    payload = {
        'entities': {
            'authors': [str(AUTHOR_ID)],
            'institutions': [],
            'sources': [],
            'works': [],
            'concepts': [],
        },
        'flower_name': '',  # Force the flower-name resolution path.
    }
    data = urllib.parse.urlencode(
        {'data': json.dumps(payload)}).encode('utf-8')
    req = urllib.request.Request(WEBAPP + '/submit/', data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            html = r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'  {FAIL} POST /submit/ failed: {e}')
        return False
    if r.status != 200 or '<html' not in html.lower():
        print(f'  {FAIL} unexpected response: status={r.status}, '
              f'first 200 chars: {html[:200]!r}')
        return False
    print(f'  {PASS} /submit rendered ({len(html)} bytes)')
    print(f'  {SKIP} manual check: open the webapp in a browser, render a '
          f'flower, and confirm the Network tab shows NO requests to '
          f'api.openalex.org')
    return True


def main():
    print(f'KONIGSBERG_URL = {KB}')
    print(f'WEBAPP_URL     = {WEBAPP or "(skipped)"}')
    results = [
        check_get_names(),
        check_get_paper_info(),
        check_batch(),
        check_webapp_submit(),
    ]
    failures = sum(1 for r in results if r is False)
    print()
    if failures:
        print(f'{FAIL} {failures} check(s) failed')
        sys.exit(1)
    print(f'{PASS} all checks passed')


if __name__ == '__main__':
    main()
