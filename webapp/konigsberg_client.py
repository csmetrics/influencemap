import requests


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
    ):
        params = {}
        
        for name in ['author_ids', 'affiliation_ids',
                     'conference_series_ids', 'journal_ids',
                     'field_of_study_ids', 'paper_ids']:
            ids = locals()[name]
            if ids:
                params[name.replace('_', '-')] = ','.join(map(str, ids))

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

        response = self.session.get(self.url, params=params)
        response.raise_for_status()
        return response.json()
