import copy
import json
import math
from collections import Counter

import flask
from flask import request
from flask_cors import CORS, cross_origin

import core.utils.entity_type as ent
from core.search.query_info import paper_info_db_check_multiquery, papers_prop_query
from core.search.query_name import (
    affiliation_name_query, author_name_query, conference_name_query,
    fos_name_query, get_conf_journ_display_names, journal_name_query,
    paper_name_query)
from core.search.query_paper import get_all_paper_ids
from core.utils.get_stats import get_stats
from core.utils.load_tsv import tsv_to_dict
from webapp.graph import ReferenceFlower, compare_flowers
from webapp.shortener import decode_filters, url_decode_info, url_encode_info
from webapp.utils import *

from webapp.front_end_helper import make_response_data
from webapp.konigsberg_client import KonigsbergClient

kb_client = KonigsbergClient(os.getenv('KONIGSBERG_URL', 'http://localhost:8081'))

flower_leaves = [ ('author', [ent.Entity_type.AUTH])
                , ('conf'  , [ent.Entity_type.CONF, ent.Entity_type.JOUR])
                , ('inst'  , [ent.Entity_type.AFFI])
                , ('fos'   , [ent.Entity_type.FSTD]) ]
id_helper_dict = {
    "conference": "ConferenceSeriesId",
    "journal": "JournalId",
    "institution": "AffiliationId",
    "paper": "PaperId",
    "author": "AuthorId",
    "topic": "FieldOfStudyId"
}

NUM_THREADS = 8
NUM_NODE_INFO = 5


blueprint = flask.Blueprint('views', __name__)


@blueprint.route('/autocomplete')
def autocomplete():
    entity_type = request.args.get('option')
    data = loadList(entity_type)
    return flask.jsonify(data)


@blueprint.route('/query_about')
@cross_origin()
def query_about():
    entity_type = "paper" # support paper search only
    entity_title = request.args.get('title')
    entity_title = normalize_title(entity_title)
    print("query_about", entity_type, entity_title)

    data = query_entity([entity_type], entity_title)
    papers = filter_papers(entity_title, data)
    paper_ids = [p[0][id_helper_dict[entity_type]] for p in papers]
    status_msg = "Success"
    if len(paper_ids) == 0:
        status_msg = "No matching paper found"

    num_refs = sum([p[0]["ReferenceCount"] for p in papers])
    num_cits = sum([p[0]["CitationCount"] for p in papers])
    summary = "The Influence Flowers are generated from {} matching papers ({} references and {} citations), from academic data as of December 2021.".format(
        len(paper_ids), num_refs, num_cits
    )

    doc_id = url_encode_info(paper_ids=paper_ids, name=entity_title)
    url_base = f"https://influencemap.cmlab.dev/submit/?id={doc_id}"
    res = {
        "searched_title": entity_title,
        "status": status_msg,
        "search_result": data,
        "filtered_result": papers,
        "paper_ids": paper_ids,
        "flower_url": url_base,
        "summary": summary
    }
    return flask.jsonify(res)


@blueprint.route('/query')
@cross_origin()
def query():
    entity_type = "paper" # support paper search only
    entity_title = request.args.get('title')
    entity_title = normalize_title(entity_title)
    data = filter_papers(entity_title, query_entity([entity_type], entity_title))
    paper_ids = [p[0][id_helper_dict[entity_type]] for p in data]
    status_msg = "Success"
    if len(paper_ids) == 0:
        status_msg = "No matching paper found."

    num_refs = sum([p[0]["ReferenceCount"] for p in data])
    num_cits = sum([p[0]["CitationCount"] for p in data])
    summary = "The Influence Flowers are generated from {} matching papers ({} references and {} citations), from academic data as of December 2021.".format(
        len(paper_ids), num_refs, num_cits
    )

    flower = kb_client.get_flower(
        paper_ids=paper_ids, pub_years=None, cit_years=None,
        coauthors=True, self_citations=False, max_results=50)

    rdata = make_response_data(
        flower, None, is_curated=False, flower_name=entity_title,
        selection=dict(pub_years=None, cit_years=None, coauthors=True, self_citations=False))

    doc_id = url_encode_info(paper_ids=paper_ids, name=entity_title)
    url_base = f"https://influencemap.cmlab.dev/submit/?id={doc_id}"
    rdata["status"] = status_msg
    rdata["url_base"] = url_base
    rdata["summary"] = summary

    #generate URLs for alter nodes
    for flower_type, _ in flower_leaves:
        for node in rdata[flower_type][0]["nodes"]:
            if flower_type == "author": node["url"] = url_encode_info(author_ids=[node["id"]], name=node["name"])
            if flower_type == "conf": node["url"] = url_encode_info(conference_series_ids=[node["id"]], journal_ids=[node["id"]], name=node["name"])
            if flower_type == "inst": node["url"] = url_encode_info(affiliation_ids=[node["id"]], name=node["name"])
            if flower_type == "fos": node["url"] = url_encode_info(field_of_study_ids=[node["id"]], name=node["name"])

    return flask.jsonify(rdata)


@blueprint.route('/')
def main():
    return flask.render_template("main.html")


@blueprint.route('/browse')
def browse():
    browse_list = load_gallery()
    return flask.render_template(
        "browse.html",
        browse_groups=browse_list, cache_data=[])


@blueprint.route('/create', methods=['GET', 'POST'])
def create():

    json_data = request.form.get('data')
    data = {} if json_data is None else json.loads(json_data)
    keyword = data.get('keyword', '')
    search = data.get('search') == 'true'
    option = data.get('option', '')

    # render page with data
    return flask.render_template(
        "create.html",
        navbarOption=get_navbar_option(keyword, option),
        search=search)



@blueprint.route('/curate')
def curate():
    types = get_cache_types()
    data = json.loads(request.form.get('data'))
    keyword = data.get('keyword', '')
    search = data.get('search') == 'true'
    option = data.get('option')

    # render page with data
    return flask.render_template(
        "curate.html",
        navbarOption=get_navbar_option(keyword, option),
        search=search,
        types=types)


@blueprint.route('/check_record')
def check_record():
    exists, names = check_browse_record_exists(request.form.get("type"), request.form.get("name"))
    return flask.jsonify({"exists": exists, "names": names})


@blueprint.route('/crate_load_file')
def curate_load_file():
    filename = request.form.get("filename")
    try:
        data = tsv_to_dict(filename)
        success = "true"
    except FileNotFoundError:
        data = {}
        success = "false"
    return flask.jsonify({'data': data, 'success': success})



s = {
    'author': ('<i class="fa fa-user""></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'conference': ('<i class="fa fa-building"></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'institution': ('<i class="fa fa-university"></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'journal': ('<i class="fa fa-book"></i><h4>{DisplayName}</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>'),
    'paper': ('<i class="fa fa-file"></i><h4>{OriginalTitle}</h4><p>Citations: {CitationCount}</p>'),
    'topic': ('<i class="fa fa-flask"></i><h4>{DisplayName} (Level {Level})</h4><p>Papers: {PaperCount}, Citations: {CitationCount}</p>')
}


@blueprint.route('/search', methods=['POST'])
def search():
    request_data = json.loads(request.form.get("data"))
    keyword = request_data.get("keyword")
    entityType = request_data.get("option")
    keyword = normalize_title(keyword)

    print("search", entityType, keyword)
    data = query_entity(entityType, keyword)
    for i in range(len(data)):
        entity = {'data': data[i][0]}
        entity['display-info'] = s[data[i][1]].format(**entity['data'])
        if "Affiliation" in entity['data']: entity['display-info'] = entity['display-info'][0:-4] + ", Institution: {}</p>".format(entity['data']["Affiliation"])
        if "Authors" in entity['data']: entity['display-info'] += "<p>Authors: {}</p>".format(", ".join(entity['data']["Authors"]))
        entity['table-id'] = "{}_{}".format(data[i][1], entity['data'][id_helper_dict[data[i][1]]])
        data[i] = entity
    return flask.jsonify({'entities': data})



@blueprint.route('/manualcache', methods=['POST'])
def manualcache():
    cache_dictionary = (json.loads(request.form.get('cache')))
    paper_action = request.form.get('paperAction')
    #saveNewBrowseCache(cache_dictionary)

    if paper_action == "batch":
        paper_ids = get_all_paper_ids(cache_dictionary["EntityIds"])
        addToBatch(paper_ids)
    if paper_action == "cache":
        paper_ids = get_all_paper_ids(cache_dictionary["EntityIds"])
        paper_info_db_check_multiquery(paper_ids)
    return flask.jsonify({})


@blueprint.route('/submit/', methods=['GET', 'POST'])
def submit():
    pub_years = None
    cit_years = None
    self_citations = False
    coauthors = True
    if request.method == "GET":
        doc_id = request.args["id"]
        ids, flower_name, curated_flag = url_decode_info(doc_id)
        author_ids = ids.author_ids
        affiliation_ids = ids.affiliation_ids
        conference_ids = ids.conference_series_ids
        fos_ids = ids.field_of_study_ids
        journal_ids = ids.journal_ids
        paper_ids = ids.paper_ids

        encoded_filters = request.args.get("filters")
        if encoded_filters is not None:
            decoded_filters = decode_filters(encoded_filters)
            pub_years = decoded_filters.pub_years
            cit_years = decoded_filters.cit_years
            self_citations = decoded_filters.self_citations
            coauthors = decoded_filters.coauthors
    else:
        curated_flag = False
        data_str = request.form['data']
        data = json.loads(data_str)
        entities = data['entities']
        author_ids = list(map(int, entities['AuthorIds']))
        affiliation_ids = list(map(int, entities['AffiliationIds']))
        conference_ids = list(map(int, entities['ConferenceIds']))
        journal_ids = list(map(int, entities['JournalIds']))
        paper_ids = list(map(int, entities['PaperIds']))
        fos_ids = list(map(int, entities['FieldOfStudyIds']))

        flower_name = data.get('flower_name')
        doc_id = url_encode_info(
            author_ids=author_ids, affiliation_ids=affiliation_ids,
            conference_series_ids=conference_ids, field_of_study_ids=fos_ids,
            journal_ids=journal_ids, paper_ids=paper_ids, name=flower_name)

    if not flower_name:
        first_nonempty_id_list = (author_ids or affiliation_ids
                                  or conference_ids or journal_ids
                                  or paper_ids or fos_ids)
        if not first_nonempty_id_list:
            raise ValueError('no entities')
        name_lookup_f = {
            id(author_ids): author_name_query,
            id(affiliation_ids): affiliation_name_query,
            id(conference_ids): conference_name_query,
            id(journal_ids): journal_name_query,
            id(paper_ids): paper_name_query,
            id(fos_ids): fos_name_query}[id(first_nonempty_id_list)]
        flower_name = name_lookup_f([first_nonempty_id_list[0]])[0]
        total_entities = (len(author_ids) + len(affiliation_ids)
                          + len(conference_ids) + len(journal_ids)
                          + len(paper_ids) + len(fos_ids))
        if total_entities > 1:
            flower_name += f" +{total_entities - 1} more"

    flower = kb_client.get_flower(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        conference_series_ids=conference_ids, field_of_study_ids=fos_ids,
        journal_ids=journal_ids, paper_ids=paper_ids, pub_years=pub_years,
        cit_years=cit_years, coauthors=coauthors,
        self_citations=self_citations, max_results=50)

    stats = kb_client.get_stats(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        conference_series_ids=conference_ids, field_of_study_ids=fos_ids,
        journal_ids=journal_ids, paper_ids=paper_ids)

    url_base = f"https://influencemap.cmlab.dev/submit/?id={doc_id}"

    session = dict(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        conference_ids=conference_ids, journal_ids=journal_ids,
        fos_ids=fos_ids, paper_ids=paper_ids, flower_name=flower_name,
        url_base=url_base, icoauthor=coauthors, self_cite=self_citations,
        year_ranges=None)

    rdata = make_response_data(
        flower, stats, is_curated=curated_flag, flower_name=flower_name,
        session=session, selection=dict(
            pub_years=pub_years, cit_years=cit_years, coauthors=coauthors,
            self_citations=self_citations))
    return flask.render_template("flower.html", **rdata)


@blueprint.route('/resubmit/', methods=['POST'])
def resubmit():
    # option = request.form.get('option')
    # keyword = request.form.get('keyword')
    # flower_config['reference'] = request.form.get('cmp_ref') == 'true'
    # flower_config['num_leaves'] = int(request.form.get('numpetals'))
    # flower_config['order'] = request.form.get('petalorder')

    session = json.loads(request.form.get("session"))
    flower_name  = session['flower_name']
    author_ids = session['author_ids']
    affiliation_ids = session['affiliation_ids']
    conference_ids = session['conference_ids']
    journal_ids = session['journal_ids']
    fos_ids = session['fos_ids']
    paper_ids = session['paper_ids']

    self_citations = request.form.get('selfcite') == 'true'
    coauthors = request.form.get('coauthor') == 'true'
    pub_lower = int(request.form.get('from_pub_year'))
    pub_upper = int(request.form.get('to_pub_year'))
    cit_lower = int(request.form.get('from_cit_year'))
    cit_upper = int(request.form.get('to_cit_year'))
    session['year_ranges'] = {
        'pub_lower': pub_lower,
        'pub_upper': pub_upper,
        'cit_lower': cit_lower,
        'cit_upper': cit_upper
    }

    flower = kb_client.get_flower(
        author_ids=author_ids, affiliation_ids=affiliation_ids,
        conference_series_ids=conference_ids, field_of_study_ids=fos_ids,
        journal_ids=journal_ids, paper_ids=paper_ids,
        pub_years=(pub_lower, pub_upper), cit_years=(cit_lower, cit_upper),
        coauthors=coauthors, self_citations=self_citations, max_results=50)

    rdata = make_response_data(
        flower, flower_name=flower_name, session=session)

    return flask.jsonify(rdata)


def conf_journ_to_display_names(papers):
    conf_journ_ids = {"ConferenceSeriesIds": [], "JournalIds": []}
    for paper in papers.values():
        if "ConferenceSeriesId" in paper: conf_journ_ids["ConferenceSeriesIds"].append(paper["ConferenceSeriesId"])
        if "JournalId" in paper: conf_journ_ids["JournalIds"].append(paper["JournalId"])
    conf_journ_display_names = get_conf_journ_display_names(conf_journ_ids)
    for paper in papers.values():
        if "ConferenceSeriesId" in paper:
            paper["ConferenceName"] = conf_journ_display_names["Conference"][paper["ConferenceSeriesId"]]
        if "JournalId" in paper:
            paper["JournalName"] = conf_journ_display_names["Journal"][paper["JournalId"]]
    return papers


@blueprint.route('/get_publication_papers')
def get_publication_papers():
    request_data = json.loads(request.form.get("data_string"))
    session = request_data.get("session")

    pub_year_min = int(request.form.get("pub_year_min"))
    pub_year_max = int(request.form.get("pub_year_max"))
    paper_ids = session['cache']
    papers = paper_info_db_check_multiquery(paper_ids)
    papers = [paper for paper in papers if (paper["Year"] >= pub_year_min and paper["Year"] <= pub_year_max)]
    papers = conf_journ_to_display_names({paper["PaperId"]: paper for paper in papers})
    return flask.jsonify({"papers": papers, "names": session["entity_names"]+ session["node_info"]})


@blueprint.route('/get_citation_papers')
def get_citation_papers():
    # request should contain the ego author ids and the node author ids separately
    request_data = json.loads(request.form.get("data_string"))
    session = request_data.get("session")

    cite_year_min = int(request.form.get("cite_year_min"))
    cite_year_max = int(request.form.get("cite_year_max"))
    pub_year_min = int(request.form.get("pub_year_min"))
    pub_year_max = int(request.form.get("pub_year_max"))
    paper_ids = session['cache']
    papers = paper_info_db_check_multiquery(paper_ids)
    cite_papers = [[citation for citation in paper["Citations"] if (citation["Year"] >= cite_year_min and citation["Year"] <= cite_year_max)] for paper in papers if (paper["Year"] >= pub_year_min and paper["Year"] <= pub_year_max)]
    citations = sum(cite_papers,[])
    citations = conf_journ_to_display_names({paper["PaperId"]: paper for paper in citations})

    return flask.jsonify({"papers": citations, "names": session["entity_names"] + session["node_info"],"node_info": session["node_information_store"]})


def get_entities(paper):
    ''' Gets the entities of a paper
    '''
    authors      = [author["AuthorName"] for author in paper["Authors"]]
    affiliations = [author["AffiliationName"] for author in paper["Authors"] if "AffiliationName" in author]
    conferences = [paper["ConferenceName"]] if ("ConferenceName" in paper) else []
    journals = [paper["JournalName"]] if ("JournalName" in paper) else []
    fieldsofstudy = [fos["FieldOfStudyName"] for fos in paper["FieldsOfStudy"] if fos["FieldOfStudyLevel"] == 1] if ("FieldsOfStudy" in paper) else []

    return authors, affiliations, conferences, journals, fieldsofstudy


NODE_INFO_FIELDS = ["PaperTitle", "Authors", "PaperId", "Year", "ConferenceName",
        "ConferenceSeriesId", "JournalName", "JournalId"]


def get_node_info_single(entity_id, entity_type, year_ranges):
    # Determine the citation range
    pub_lower = cit_lower = pub_upper = cit_upper = None
    if year_ranges:
        pub_lower = year_ranges["pub_lower"]
        pub_upper = year_ranges["pub_upper"]
        cit_lower = year_ranges["cit_lower"]
        cit_upper = year_ranges["cit_upper"]

    # Get node info
    request_data = json.loads(request.form.get("data_string"))
    session = request_data.get("session")

    # Get coauthors list to filter
    if session['icoauthor'] == 'false':
        coauthors = session['coauthors']
    else:
        coauthors = list()

    # Get self_citation list to filter
    if session['self_cite'] == 'false':
        self = session['entity_names']
    else:
        self = list()

    node_type_id = [l[0] for l in flower_leaves].index(entity_type)

    node_info = kb_client.get_node_info(
        node_id=entity_id, node_type=node_type_id,
        author_ids=session["author_ids"], affiliation_ids=session["affiliation_ids"],
        conference_series_ids=session["conference_ids"], field_of_study_ids=session["fos_ids"],
        journal_ids=session["journal_ids"], paper_ids=session["paper_ids"],
        pub_years=(pub_lower, pub_upper), cit_years=(cit_lower, cit_upper),
        coauthors=coauthors, self_citations=self, max_results=50)

    # Results
    # papers_to_send = dict()
    # links = dict()
    #
    # for paper in papers:
    #     # Publication range filter
    #     if (pub_lower and paper["Year"] < pub_lower) or \
    #         (pub_upper and paper["Year"] > pub_upper):
    #         continue
    #
    #     for link_type in ["References", "Citations"]:
    #         for rel_paper in paper[link_type]:
    #             # Citation range filter
    #             if link_type == "Citations" and \
    #                 ((cit_lower and rel_paper["Year"] < cit_lower) or \
    #                 (cit_upper and rel_paper["Year"] > cit_upper)):
    #                             continue
    #
    #             # Get fields
    #             auth, inst, conf, jour, fos = get_entities(rel_paper)
    #             fields = dict()
    #             fields['author'] = set(auth)
    #             fields['inst'] = set(inst)
    #             fields['conf'] = set(conf + jour)
    #             fields['fos']  = set(fos)
    #
    #             check = dict()
    #             check['author'] = coauthors + self
    #             check['inst'] = coauthors + self
    #             check['conf'] = coauthors
    #             check['fos']  = list()
    #
    #             skip = False
    #             for n_type, check_val in check.items():
    #                 if not set(check_val).isdisjoint(fields[entity_type]):
    #                     skip = True
    #                     break
    #             if skip:
    #                 continue
    #
    #             if entity not in fields[entity_type]:
    #                 continue
    #
    #             papers_to_send[paper["PaperId"]] = {k:v for k,v in paper.items() if k in NODE_INFO_FIELDS}
    #             papers_to_send[paper["PaperId"]] = add_author_order(papers_to_send[paper["PaperId"]])
    #
    #             papers_to_send[rel_paper["PaperId"]] = {k:v for k,v in rel_paper.items() if k in NODE_INFO_FIELDS}
    #             papers_to_send[rel_paper["PaperId"]] = add_author_order(papers_to_send[rel_paper["PaperId"]])
    #
    #             if link_type == "Citations":
    #                 if paper["PaperId"] in links:
    #                     links[paper["PaperId"]]["reference"].append(rel_paper["PaperId"])
    #                 else:
    #                     links[paper["PaperId"]] = {"reference": [rel_paper["PaperId"]], "citation": list()}
    #             else:
    #                 if paper["PaperId"] in links:
    #                     links[paper["PaperId"]]["citation"].append(rel_paper["PaperId"])
    #                 else:
    #                     links[paper["PaperId"]] = {"citation": [rel_paper["PaperId"]], "reference": list()}
    #
    # paper_sort_func = lambda x: -papers_to_send[x]["Year"]
    # links = sorted([{"citation": sorted(link["citation"],key=paper_sort_func), "reference": sorted(link["reference"],key=paper_sort_func), "ego_paper": key} for key, link in links.items()], key=lambda x: paper_sort_func(x["ego_paper"]))

    links = [{"ego_paper": id, "reference": v["reference"], "citation": v["citation"]} for id, v in node_info.items()]

    return {"node_links": links}


def get_paper_info(data):
    papers = set()
    for d in data:
        papers.update(set([d["ego_paper"]] + d["citation"] + d["reference"]))
    paper_info = papers_prop_query(list(papers))
    return paper_info


@blueprint.route('/get_node_flower/', methods=['POST'])
def get_node_flower():
    request_data = json.loads(request.form.get("data_string"))

    flower_name = request_data.get("name")
    flower_type = request_data.get("node_type")
    node_ids = request_data.get("ids")
    id_list = [int(id) for id in node_ids.split(',')]

    if flower_type == "author": doc_id = url_encode_info(author_ids=id_list, name=flower_name)
    if flower_type == "conf": doc_id = url_encode_info(conference_series_ids=id_list, journal_ids=id_list, name=flower_name)
    if flower_type == "inst": doc_id = url_encode_info(affiliation_ids=id_list, name=flower_name)
    if flower_type == "fos": doc_id = url_encode_info(field_of_study_ids=id_list, name=flower_name)

    data = dict()
    data["flower_url"] = f"https://influencemap.cmlab.dev/submit/?id={doc_id}"
    data["flower_name"] = flower_name
    return flask.jsonify(data)


@blueprint.route('/get_node_info/', methods=['POST'])
def get_node_info():
    request_data = json.loads(request.form.get("data_string"))
    node_name = request_data.get("name")
    node_type = request_data.get("node_type")
    node_ids = request_data.get("ids")
    session = request_data.get("session")
    year_ranges = session["year_ranges"]
    flower_name = session["flower_name"]

    data = get_node_info_single(node_ids, node_type, year_ranges)
    data["node_name"] = node_name
    data["flower_name"] = flower_name
    data["max_page"] = math.ceil(len(data["node_links"]) / 5)
    data["node_links"] = data["node_links"][0:min(5, len(data["node_links"]))]
    data["paper_info"] = get_paper_info(data["node_links"])
    return flask.jsonify(data)



@blueprint.route('/get_next_node_info_page/', methods=['POST'])
def get_next_node_info_page():
    request_data = json.loads(request.form.get("data_string"))
    node_name = request_data.get("name")
    node_type = request_data.get("node_type")
    node_ids = request_data.get("ids")
    session = request_data.get("session")
    year_ranges = session["year_ranges"]
    page = int(request_data.get("page"))

    node_info = get_node_info_single(node_ids, node_type, year_ranges)
    page_length = 5
    data = {"node_links": node_info["node_links"][0+page_length*(page-1):min(page_length*page, len(node_info["node_links"]))]}
    data["paper_info"] = get_paper_info(data["node_links"])
    return flask.jsonify(data)
