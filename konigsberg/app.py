import flask

import flowers

app = flask.Flask(__name__)

florist = flowers.Florist('bingraph')


def _get_ids_from_request(argname):
    ids_str = flask.request.args.get(argname, '')
    try:
        return list(map(int, filter(None, ids_str.split(','))))
    except ValueError:
        flask.abort(400)


def _get_bool_from_request(argname):
    return bool(flask.request.args.get(argname, ''))


def _get_range_from_request(argname):
    range_str = flask.request.args.get(argname, '')
    if not range_str:
        return None
    try:
        start_year, end_year = range_str.split(',')
        start_year = int(start_year)
        end_year = int(end_year)
    except ValueError:
        flask.abort(400)
    return start_year, end_year


def result_arrays_as_dict(result_arrays):
    return {
        str(id_): float(score)
        for id_, score in zip(result_arrays.ids, result_arrays.scores)
    }


def part_flower_as_dict(part_flower):
    return {
        'influencers': result_arrays_as_dict(part_flower.influencers),
        'influencees': result_arrays_as_dict(part_flower.influencees),
    }


def flower_as_dict(flower):
    return {
        'author_part': part_flower_as_dict(flower.author_part),
        'affiliation_part': part_flower_as_dict(flower.affiliation_part),
        'field_of_study_part': part_flower_as_dict(flower.field_of_study_part),
        'journal_part': part_flower_as_dict(flower.journal_part),
        'conference_series_part':
            part_flower_as_dict(flower.conference_series_part),
    }


@app.route('/get-flower')
def get_flower():
    author_ids = _get_ids_from_request('author-ids')
    affiliation_ids = _get_ids_from_request('affiliation-ids')
    field_of_study_ids = _get_ids_from_request('field-of-study-ids')
    journal_ids = _get_ids_from_request('journal-ids')
    conference_series_ids = _get_ids_from_request('conference-series-ids')

    self_citations = _get_bool_from_request('self-citations')
    exclude_coauthors = _get_bool_from_request('exclude-coauthors')

    pub_years = _get_range_from_request('pub-years')
    cit_years = _get_range_from_request('cit-years')

    flower = florist.get_flower(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        field_of_study_ids=field_of_study_ids, journal_ids=journal_ids,
        conference_series_ids=conference_series_ids,
        self_citations=self_citations, coauthors=not exclude_coauthors,
        pub_years=pub_years, cit_years=cit_years)

    return flask.jsonify(flower_as_dict(flower))


if __name__ == '__main__':
    app.run('127.0.0.1', debug=True)
