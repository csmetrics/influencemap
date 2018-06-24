'''
Functions for querying database for specific information:
  - Author information (Create generator function to query papers?)
  - Paper information

Each query goes through a cache layer before presenting information.

date:   19.06.18
author: Alexander Soen
'''

import pandas as pd
from graph.config import conf
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from graph.schema_cache import PaperInfo
from datetime import datetime


def from_query(query, q_key, res_dict, r_key):
    try:
        res_dict[r_key] = query[q_key]
    except KeyError:
        res_dict[r_key] = None


def nan_to_none(df):
    ''' Convert dataframe with NaN values to None.
    '''
    return df.where((pd.notnull(df)), None)


def author_name_db_query(author_name):
    '''
    Query database for results.

    TODO: Add query limit for papers, possibly return generator to continuously
          query for new papers.
    '''
    # Normalise author name
    author_name = author_name.lower()

    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))
    
    # Search for authors
    authors_targets = ['AuthorId', 'NormalizedName', 'DisplayName']

    authors_s = Search(index = 'authors', using = client)
    authors_s = authors_s.query('match_phrase', NormalizedName = author_name)
    authors_s = authors_s.source(authors_targets)

    # Convert authors to dictionary format
    authors_list = list()
    for authors in authors_s.scan():
        row_dict = dict()
        for target in authors_targets:
            from_query(authors, target, row_dict, target)
            #row_dict[target] = authors[target]

        authors_list.append(row_dict)

    # Authors dataframe
    authors_df = pd.DataFrame(authors_list)
    
    # Check for empty results
    if authors_df.empty:
        # Return None
        return None
    
    # Author IDs to search over PAA
    author_ids = authors_df['AuthorId']

    paa_list = list()
    paa_targets = ['AuthorId', 'PaperId']

    # For each of the authors ids
    for author_id in author_ids:
        # Search PAA database for papers
        paa_s = Search(index = 'paperauthoraffiliations', using = client)
        paa_s = paa_s.query('match', AuthorId = author_id)
        paa_s = paa_s.source(paa_targets)

        # Convert to dictionary format
        for paa in paa_s.scan():
            row_dict = dict()
            for target in paa_targets:
                from_query(paa, target, row_dict, target)
                row_dict[target] = paa[target]

            paa_list.append(row_dict)

    # PAA dataframe
    paa_df = pd.DataFrame(paa_list)

    # Return join of dataframes
    res_df = pd.merge(authors_df, paa_df, how = 'inner', on = 'AuthorId')
    return None if res_df.empty else res_df


def paper_prop_query(paper_id_list):
    ''' Generates pandas dataframe for all fields in paper_info cache apart
        from citation and reference information.
    '''
    # Remove duplicates in paper id list
    paper_id_list = list(set(paper_id_list))

    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    papers_list = list()
    paa_list    = list()

    # Targets
    papers_targets = ['PaperId', 'ConferenceInstanceId', 'JournalId', 'Year']
    paa_targets    = ['PaperId', 'AuthorId', 'AffiliationId']

    # Iterate through the paper ids
    for paper_id in paper_id_list:
        # Query for papers
        papers_s = Search(index = 'papers', using = client)
        papers_s = papers_s.query('match', PaperId = paper_id)
        papers_s = papers_s.source(papers_targets)

        # Query for paper affiliation
        paa_s = Search(index = 'paperauthoraffiliations', using = client)
        paa_s = paa_s.query('match', PaperId = paper_id)
        paa_s = paa_s.source(paa_targets)

        # Convert papers into dictionary format
        for paper in papers_s.scan():
            row_dict = dict()
            for target in papers_targets:
                from_query(paper, target, row_dict, target)
                #row_dict[target] = paper[target]

            papers_list.append(row_dict)

        # Convert paa into dictionary format
        for paa in paa_s.scan():
            row_dict = dict()
            for target in paa_targets:
                from_query(paa, target, row_dict, target)
                #row_dict[target] = paa[target]

            paa_list.append(row_dict)

    # After parsing paper ids, convert into dataframes and join
    papers_df = pd.DataFrame(papers_list, columns = papers_targets)
    paa_df    = pd.DataFrame(paa_list   , columns = paa_targets)

    # Renaming conference
    papers_df = papers_df.rename(columns = \
                    {'ConferenceInstanceId': 'ConferenceId'})

    res_df = pd.merge(papers_df, paa_df, how = 'inner', on = 'PaperId')
    return res_df


def paper_cite_info_query(paper_id_list):
    ''' Generates pandas dataframe for all fields in paper_info cache apart
        from citation and reference information.
    '''
    # Remove duplicates in paper id list
    paper_id_list = list(set(paper_id_list))

    # Elastic search client
    client = Elasticsearch(conf.get("elasticsearch.hostname"))

    # Query fields
    ref_f    = ['PaperId', 'PaperReferenceId']
    #col_name = ['PaperTo', 'PaperFrom'] #TODO Verify ordering here is correct

    cite_info_list = list()
    cite_me = list()
    me_cite = list()
    
    for paper_id in paper_id_list:
        pref_s = Search(index = 'paperreferences', using = client)
        pref_s = pref_s.query('multi_match', query = paper_id, fields = ref_f)

        # Convert into dictionary format
        for cite_info in pref_s.scan():
            row_dict = dict()

            # Determine what type of citation
            if paper_id == cite_info[ref_f[0]]:
                row_dict['PaperId'] = cite_info[ref_f[1]]
                cite_me.append(row_dict)
            else:
                row_dict['PaperId'] = cite_info[ref_f[0]]
                me_cite.append(row_dict)


    # After parsing paper ids, convert into dataframes
    ref  = pd.DataFrame(me_cite, columns = ['PaperId'])
    cite = pd.DataFrame(cite_me, columns = ['PaperId'])
    return ref, cite


def paper_ids_db_query(paper_id_list):
    ''' Generates pandas dataframe for paper_info
    '''
    #res_dict = dict()
    res_list = list()

    # Iterate through paper ids
    for paper_id in paper_id_list:
        # Get properties
        paper_prop = paper_prop_query([paper_id])

        # Check if properties empty
        if paper_prop.empty:
            continue

        # Get paper links
        ref, cite  = paper_cite_info_query([paper_id])

        # Get properties of citation papers
        ref  = paper_prop_query(list(ref['PaperId']))
        cite = paper_prop_query(list(cite['PaperId']))

        # Put data into dictionary format, also convert nan to none
        paper_res = dict()
        paper_res['Properties'] = nan_to_none(paper_prop)
        paper_res['References'] = nan_to_none(ref)
        paper_res['Citations']  = nan_to_none(cite)

        # Add to result dictionary
        #res_dict[paper_id] = paper_res
        res_list.append(paper_res)

    return res_list #res_dict


def df_to_doc_dict(df, targets):
    ''' Converts dataframe into list of dictionary of targets.
    '''
    # Subcolumns of properties for authors
    sub_df = df[targets].drop_duplicates()

    res_list = list()

    # Iterate through the author information
    for _, row in sub_df.iterrows():
        row_dict = dict()
        for target in targets:
            row_dict[target] = row[target]

        res_list.append(row_dict)
    
    return res_list


def paper_df_to_doc(paper_df_dict):
    ''' Converts from dictionary of pandas dataframes to PaperInfo DocType.
    '''
    paper = PaperInfo()

    # Target lists
    property_targets = ['PaperId', 'ConferenceId', 'JournalId', 'Year']
    author_targets = ['AuthorId', 'AffiliationId']

    # Property values
    paper_id      = list(paper_df_dict['Properties']['PaperId'])[0]
    conference_id = list(paper_df_dict['Properties']['ConferenceId'])[0]
    journal_id    = list(paper_df_dict['Properties']['JournalId'])[0]
    year          = list(paper_df_dict['Properties']['Year'])[0]

    # Update property values
    paper.meta.id      = paper_id
    paper.PaperId      = paper_id
    paper.ConferenceId = conference_id
    paper.JournalId    = journal_id
    paper.Year         = year

    # Authors
    paper.Authors = df_to_doc_dict(paper_df_dict['Properties'], author_targets)

    # Do same as above for each reference paper
    ref_list = list()
    ref_gp = paper_df_dict['References'].astype(str).groupby(property_targets)
    for ref_prop, ref_df in ref_gp:
        print(ref_df)
        ref_dict = dict()

        # Add properties
        for prop, val in zip(property_targets, ref_prop):
            ref_dict[prop] = val
    
        # Add authors
        ref_dict['Authors'] = df_to_doc_dict(ref_df, author_targets)
        print(ref_dict)
        
        ref_list.append(ref_dict)

    # Do same as above for each citation paper
    cite_list = list()
    cite_gp = paper_df_dict['Citations'].astype(str).groupby(property_targets)
    for cite_prop, cite_df in cite_gp:
        cite_dict = dict()

        # Add properties
        for prop, val in zip(property_targets, cite_prop):
            cite_dict[prop] = val
    
        # Add authors
        cite_dict['Authors'] = df_to_doc_dict(cite_df, author_targets)
        
        cite_list.append(cite_dict)

    print(cite_list)
    # Attach reference and citations lists to paper
    paper.References = ref_list
    paper.Citations  = cite_list

    # Creation date
    paper.CreatedDate = datetime.now()

    return paper


def paper_doc_to_df(paper_doc):
    ''' Converts from PaperInfo DocType into dictionary of pandas dataframe
        format.
    '''
    # Target lists
    property_targets    = ['PaperId', 'ConferenceId', 'JournalId', 'Year']
    author_targets      = ['AuthorId', 'AffiliationId']
    link_author_targets = ['PaperId', 'AuthorId', 'AffiliationId']

    paper_id      = paper_doc.PaperId
    conference_id = paper_doc.ConferenceId
    journal_id    = paper_doc.JournalId
    year          = paper_doc.Year

    # Generate the property dataframe
    properties_df = pd.DataFrame(list(paper_doc.Authors), columns = author_targets)
    properties_df['PaperId']      = paper_id
    properties_df['ConferenceId'] = conference_id
    properties_df['JournalId']    = journal_id
    properties_df['Year']         = year

    # Generate the reference dataframe
    ref_prop_list = list()
    ref_auth_list = list()
    for ref in paper_doc.References:
        # Get Author information
        add_pid = lambda x: {'PaperId': ref.PaperId, 'AuthorId': x.AuthorId,
                             'AffiliationId': x.AffiliationId}

        ref_auths = list(ref.Authors)
        ref_auths = list(map(add_pid, ref_auths))
        ref_auth_list += ref_auths

        # Append rest of doc (properties)
        ref_prop = {'PaperId': ref.PaperId, 'ConferenceId': ref.ConferenceId,
                    'JournalId': ref.JournalId, 'Year': ref.Year}
        ref_prop_list.append(ref_prop)

    ref_prop = pd.DataFrame(ref_prop_list, columns = property_targets)
    ref_auth = pd.DataFrame(ref_auth_list, columns = link_author_targets)

    references_df = pd.merge(ref_prop, ref_auth, how = 'inner', on = 'PaperId')

    # Generate the reference dataframe
    cite_prop_list = list()
    cite_auth_list = list()
    for cite in paper_doc.Citations:
        # Get Author information
        add_pid = lambda x: {'PaperId': cite.PaperId, 'AuthorId': x.AuthorId,
                             'AffiliationId': x.AffiliationId}

        cite_auths = list(cite.Authors)
        cite_auths = list(map(add_pid, cite_auths))
        cite_auth_list += cite_auths

        # Append rest of doc (properties)
        cite_prop = {'PaperId': cite.PaperId, 'ConferenceId': cite.ConferenceId,
                     'JournalId': cite.JournalId, 'Year': cite.Year}
        cite_prop_list.append(cite_prop)

    cite_prop = pd.DataFrame(cite_prop_list, columns = property_targets)
    cite_auth = pd.DataFrame(cite_auth_list, columns = link_author_targets)

    citations_df = pd.merge(cite_prop, cite_auth, how = 'inner', on = 'PaperId')

    res_dict = dict()
    res_dict['Properties'] = properties_df
    res_dict['References'] = references_df
    res_dict['Citations']  = citations_df

    return res_dict


if __name__ == '__main__':
    # TESTING
    author_df = author_name_db_query('antony l hosking')
    print(author_df)

    a_papers = list(author_df['PaperId'])
    paper_ids = paper_ids_db_query(a_papers)
    print(paper_ids)

    from elasticsearch_dsl.connections import connections
    connections.create_connection(hosts = conf.get("elasticsearch.hostname"), timeout=20)

    for paper_id in paper_ids:
        paper_doc = paper_df_to_doc(paper_id)
        print(paper_doc)
        print(paper_id)
        print('>')
        print(paper_doc_to_df(paper_doc))
        print('\n---\n')
        paper_doc.save()
