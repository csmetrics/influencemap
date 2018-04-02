


#def auth_name_to_paper_map(auth_name):
#    """
#    """
#    query = {
#        "path": "/author",
#        "author": {
#            "type": "Author",
#            "match": {
#                "Name": auth_name
#                },
#            "select": [ "DisplayAuthorName", "PaperIDs" ]
#            }
#        }
#
#    data = query_academic_search('post', JSON_URL, query)
#    res_dict = dict()
#    name_dict = dict()
#    for entity in data['Results']:
#        res_dict[entity[0]['CellID']] = entity[0]['PaperIDs']
#        try:
#            name_dict[entity[0]['DisplayAuthorName']] += 1
#        except KeyError:
#            name_dict[entity[0]['DisplayAuthorName']] = 1
#
#    return sorted(name_dict.items(), key=operator.itemgetter(1),
#                  reverse=True)[0][0], res_dict
#

def entity_to_citation_score(entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_id = entity.entity_id
    e_type = entity.entity_type
    paper_ids = entity.paper_df['paper_id'].tolist()

    query = {
        "path": "/paper/CitationIDs/cites",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            },
        "cites": {
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for ego, cite in data['Results']:
        row = dict()
        row['info_from'] = ego['CellID']
        #row['paper_other'] = cite['CellID']
        row['paper_id'] = cite['CellID']
        row['influenced'] = 1 #/ len(ego['AuthorIDs'])
        row['influencing'] = 0
        row['self_cite'] = 0 if entity_id in cite['AuthorIDs'] else 1
        #row['date_ego'] = ego['PublishDate']
        row['influence_date'] = to_datetime(cite['PublishDate'])
        data_sc.append(row)

    return pd.DataFrame(data_sc)


def entity_to_reference_score(entity):
    """
        Turns an author ids into a list of papers associated to the ids.
    """
    entity_id = entity.entity_id
    e_type = entity.entity_type
    paper_ids = entity.paper_df['paper_id'].tolist()

    query = {
        "path": "/paper/ReferenceIDs/refs",
        "paper": {
            "type": "Paper",
            "id": paper_ids,
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            },
        "refs": {
            "select": [
                "PublishDate",
                e_type.api_id
                ]
            }
        }

    data = query_academic_search('post', JSON_URL, query)
    data_sc = list()
    for ego, refs in data['Results']:
        row = dict()
        row['info_from'] = ego['CellID']
        #row['paper_other'] = refs['CellID']
        row['paper_id'] = refs['CellID']
        row['influenced'] = 0
        row['influencing'] = 1 #/ len(refs['AuthorIDs'])
        row['self_cite'] = 0 if entity_id in cite['AuthorIDs'] else 1
        row['influence_date'] = to_datetime(ego['PublishDate'])
        #row['influence_year'] = cite['PublishDate']
        data_sc.append(row)

    return pd.DataFrame(data_sc)


#def paper_id_to_citation_score(paper_map, entity):
#    """
#        Turns an author ids into a list of papers associated to the ids.
#    """
#    entity_ids = set(paper_map.keys())
#    paper_ids = list(itertools.chain.from_iterable(paper_map.values()))
#
#    query = {
#        "path": "/paper/CitationIDs/cites",
#        "paper": {
#            "type": "Paper",
#            "id": paper_ids,
#            "select": [
#                "PublishDate",
#                entity.api_id
#                ]
#            },
#        "cites": {
#            "select": [
#                "PublishDate",
#                entity.api_id
#                ]
#            }
#        }
#
#    data = query_academic_search('post', JSON_URL, query)
#    data_sc = list()
#    for ego, cite in data['Results']:
#        row = dict()
#        row['info_from'] = ego['CellID']
#        #row['paper_other'] = cite['CellID']
#        row['paper_id'] = cite['CellID']
#        row['influenced'] = 1 #/ len(ego['AuthorIDs'])
#        row['influencing'] = 0
#        row['self_cite'] = 0 if entity_ids.isdisjoint(cite['AuthorIDs']) else 1
#        #row['date_ego'] = ego['PublishDate']
#        row['influence_date'] = to_datetime(cite['PublishDate'])
#        data_sc.append(row)
#
#    return pd.DataFrame(data_sc)
#
#
#def paper_id_to_reference_score(paper_map, entity):
#    """
#        Turns an author ids into a list of papers associated to the ids.
#    """
#    entity_ids = set(paper_map.keys())
#    paper_ids = list(itertools.chain.from_iterable(paper_map.values()))
#
#    query = {
#        "path": "/paper/ReferenceIDs/refs",
#        "paper": {
#            "type": "Paper",
#            "id": paper_ids,
#            "select": [
#                "PublishDate",
#                entity.api_id
#                ]
#            },
#        "refs": {
#            "select": [
#                "PublishDate",
#                entity.api_id
#                ]
#            }
#        }
#
#    data = query_academic_search('post', JSON_URL, query)
#    data_sc = list()
#    for ego, refs in data['Results']:
#        row = dict()
#        row['info_from'] = ego['CellID']
#        #row['paper_other'] = refs['CellID']
#        row['paper_id'] = refs['CellID']
#        row['influenced'] = 0
#        row['influencing'] = 1 #/ len(refs['AuthorIDs'])
#        row['self_cite'] = 0 if entity_ids.isdisjoint(refs['AuthorIDs']) else 1
#        row['influence_date'] = to_datetime(ego['PublishDate'])
#        #row['influence_year'] = cite['PublishDate']
#        data_sc.append(row)
#
#    return pd.DataFrame(data_sc)


#def gen_score_df(citation_df, reference_df):
#    """
#    """
#    return pd.concat([citation_df, reference_df])


def get_influence_df(entity):
    """
    """
    cache_path = os.path.join(CACHE_DIR, entity.cache_str())

    try:
        influence_df = pd.read_pickle(cache_path)

    except FileNotFoundError:
        cites = entity_to_citation_score(entity)
        refs = entity_to_reference_score(entity)

        influence_df = pd.concat([cites, refs])

        influence_df.to_pickle(cache_path)
        os.chmod(cache_path, 0o777)

    return influence_df


def get_filtered_influence(entites, filters):
    """
    """
    influence_list = list()
    for entity in entities:
        info_df = get_influence_df(entity)

        try:
            ignores = filters[entity.paper_id]
            info_df = info_df[~info_df['info_from'].isin(ignores)]
        except KeyError:
            pass

        influence_list.append(info_df)

    return pd.concat(influence_list)
