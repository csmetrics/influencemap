import requests


def get_ids(locals_):
    params = {}
    for name in ['author_ids', 'affiliation_ids',
                 'conference_series_ids', 'journal_ids',
                 'field_of_study_ids', 'paper_ids']:
        ids = locals_[name]
        if ids:
            params[name.replace('_', '-')] = ','.join(map(str, ids))
    return params


class KonigsbergClient:
    def __init__(self, url):
        self.session = requests.Session()
        self.url = url

    def get_flower(
        self,
        *,
        author_ids=(),
        affiliation_ids=(),
        conference_series_ids=(),
        journal_ids=(),
        field_of_study_ids=(),
        paper_ids=(),
        pub_years=None,
        cit_years=None,
        coauthors=True,
        self_citations=False,
        max_results=None,
    ):
        params = {}
        params.update(get_ids(locals()))

        if self_citations:
            params['self-citations'] = 't'
        if not coauthors:
            params['exclude-coauthors'] = 't'

        if pub_years is not None:
            start_year, end_year = pub_years
            params['pub-years'] = f'{start_year},{end_year}'
        if cit_years is not None:
            start_year, end_year = cit_years
            params['cit-years'] = f'{start_year},{end_year}'

        if max_results is not None:
            params['max-results'] = str(max_results)

        response = self.session.get(self.url + '/get-flower', params=params)
        response.raise_for_status()
        return response.json()

    def get_stats(
        self,
        *,
        author_ids=(),
        affiliation_ids=(),
        conference_series_ids=(),
        journal_ids=(),
        field_of_study_ids=(),
        paper_ids=(),
    ):
        params = get_ids(locals())
        response = self.session.get(self.url + '/get-stats', params=params)
        response.raise_for_status()
        return response.json()

    def get_names(self, entity_type, ids):
        """Look up display names for the given OpenAlex ids.

        entity_type ∈ {'authors', 'institutions', 'sources', 'concepts'}.
        Returns {int_id: display_name}. Unknown ids are omitted.
        """
        if not ids:
            return {}
        response = self.session.get(
            self.url + '/get-names',
            params={'type': entity_type, 'ids': ','.join(map(str, ids))})
        response.raise_for_status()
        return {int(k): v for k, v in response.json().items()}

    def get_paper_info(self, paper_ids):
        """Look up title/year/venue for the given paper ids.

        Returns {int_id: {'title': str, 'year': int|None, 'venue': str}}.
        """
        if not paper_ids:
            return {}
        response = self.session.get(
            self.url + '/get-paper-info',
            params={'ids': ','.join(map(str, paper_ids))})
        response.raise_for_status()
        return {int(k): v for k, v in response.json().items()}

    def get_paper_citations(self, paper_ids):
        """Look up the citing papers for each given paper id.

        Returns {int_id: [citor_paper_id, ...]}.
        """
        if not paper_ids:
            return {}
        response = self.session.get(
            self.url + '/get-paper-citations',
            params={'ids': ','.join(map(str, paper_ids))})
        response.raise_for_status()
        return {int(k): [int(x) for x in v]
                for k, v in response.json().items()}

    def get_node_info(
        self,
        *,
        node_id=None,
        node_type=None,
        author_ids=(),
        affiliation_ids=(),
        conference_series_ids=(),
        journal_ids=(),
        field_of_study_ids=(),
        paper_ids=(),
        pub_years=None,
        cit_years=None,
        coauthors=True,
        self_citations=False,
        max_results=None,
    ):
        params = get_ids(locals())
        params.update({
            'node-id': int(node_id),
            'node-type': node_type
        })
        response = self.session.get(self.url + '/get-node-info', params=params)
        response.raise_for_status()
        return response.json()
