import os, sys
from django.shortcuts import render

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'python')
sys.path.insert(0, PYTHON_DIR)

from flower_bloomer import getFlower
from mkAff import getAuthor

authors_testing = [{'name': 'brian schmidt', 'authorID': '795807D5', 'numpaper': 6, 'affiliation': 'GraduatePrograminNeurobiologyandBeh,UniversityofWashington,Seattle,WA', 'field': ['Color vision'], 'mostWeightedPaper': 'neurobiological hypothesis of color appearance and hue perception', 'publishedDate': '2014/04/01'}, {'name': 'brian p schmidt', 'authorID': '7D76C2BC', 'numpaper': 6, 'affiliation': 'Ludwig-Maximilians-Universität', 'field': ['Mode-locking', 'Spectral resolution', 'Fluorescence spectroscopy'], 'mostWeightedPaper': 'a broadband kerr shutter for femtosecond fluorescence spectroscopy', 'publishedDate': '2003/07/09'}, {'name': 'brian p schmidt', 'authorID': '8338D293', 'numpaper': 4, 'affiliation': '', 'field': ['Cosmic ray', 'Chemical composition', "Earth's magnetic field"], 'mostWeightedPaper': 'electron motion in counting gases new answers and new questions', 'publishedDate': '1988/12/15'}, {'name': 'brian p schmidt', 'authorID': '7E04BAD8', 'numpaper': 3, 'affiliation': 'ZentralinstitutfürKernforschungderAkademiederWissenschaftenderDDR,Rossendorf', 'field': [], 'mostWeightedPaper': 'the resistivity inhomogeneity and the maximum possible mean resistivity of neutron transmutation doped silicon', 'publishedDate': '1983/05/14'}, {'name': 'brian schmidt', 'authorID': '7D637BBF', 'numpaper': 2, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'system architecture and methods for facilitating client side real time auctions of advertising inventory', 'publishedDate': '2015/02/19'}, {'name': 'brian schmidt', 'authorID': '7FFF28C7', 'numpaper': 2, 'affiliation': '', 'field': ['Stereoisomerism', 'Genotype', 'Young adult'], 'mostWeightedPaper': 'oral l serine supplementation reduces production of neurotoxic deoxysphingolipids in mice and humans with hereditary sensory autonomic neuropathy type 1', 'publishedDate': '2011/12/01'}, {'name': 'brian p schmidt', 'authorID': '81432A90', 'numpaper': 2, 'affiliation': 'SektionPhysikderTechnischenUniversitätDresden,WissenschaftsbereichTheoretischePhysik', 'field': ['Transition metal'], 'mostWeightedPaper': 'effective cyclotron masses and many body effects in pd', 'publishedDate': '1981/11/01'}, {'name': 'brian p schmidt', 'authorID': '7C997D5A', 'numpaper': 1, 'affiliation': 'SektionPhysikderTechaischenUniversitätDresden', 'field': ['Thermal conduction'], 'mostWeightedPaper': 'heat conductivity measurement at v3si in the temperature range 4 2 to 80 k', 'publishedDate': '1976/07/01'}, {'name': 'brian schmidt', 'authorID': '7CFC7CA3', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'valveless regenerative thermal oxidizer for treating closed loop dryer', 'publishedDate': '2012/03/27'}, {'name': 'brian schmidt', 'authorID': '7D0E8346', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'playing with sound audio hardware and software on xbox', 'publishedDate': '2001/03/01'}, {'name': 'brian schmidt', 'authorID': '7D280F0C', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'cd versus dvd the ultimate portable storage battle', 'publishedDate': '2013'}, {'name': 'brian p schmidt', 'authorID': '7D2F1FC9', 'numpaper': 1, 'affiliation': '', 'field': ['Degrees of freedom', 'Rotating wave approximation', 'van der Waals force'], 'mostWeightedPaper': 'femtosecond quantum dynamics of photoassociation reactions the exciplex formation of mercury', 'publishedDate': '1997/05/01'}, {'name': 'brian schmidt', 'authorID': '7D7626E8', 'numpaper': 1, 'affiliation': '', 'field': ['Government'], 'mostWeightedPaper': 'perspective if not funding then teaching', 'publishedDate': '2014/07/24'}, {'name': 'brian schmidt', 'authorID': '7DC8EF3B', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'professor brian schmidt nobel laureate and arc laureate fellow', 'publishedDate': '2013/09/24'}, {'name': 'brian schmidt', 'authorID': '7DD0D98C', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'afterlife beliefs memory as immortality', 'publishedDate': '2000'}, {'name': 'brian schmidt', 'authorID': '7DF4CD18', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'laparoscopic treatment of a postoperative small bowel obstruction', 'publishedDate': '2010'}, {'name': 'brian p schmidt', 'authorID': '7E59BB1C', 'numpaper': 1, 'affiliation': '', 'field': ['Endothelial stem cell', 'Genetically modified mouse'], 'mostWeightedPaper': 'changes in markers of vascular injury in response to transient hyperhomocysteinemia', 'publishedDate': '2003/01/04'}, {'name': 'brian p schmidt', 'authorID': '7E6134DA', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'nobel lecture accelerating expansion of the universe through observations of distant supernovae', 'publishedDate': '2012/08/13'}, {'name': 'brian schmidt', 'authorID': '7F8D05C5', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'automatic music selection system', 'publishedDate': '2013/01/24'}, {'name': 'brian schmidt', 'authorID': '7FB7533B', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'elementary problems e1925 e1934', 'publishedDate': '1966'}, {'name': 'brian schmidt', 'authorID': '7FC43C33', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'measuring the properties of the donor star to tycho s sn', 'publishedDate': ''}, {'name': 'brian schmidt', 'authorID': '7FD765D4', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'system and methods for minimally invasive spine surgery', 'publishedDate': '2011/07/14'}, {'name': 'brian schmidt', 'authorID': '7FE22095', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'tonight this coterie', 'publishedDate': '2013'}, {'name': 'brian schmidt', 'authorID': '8078C615', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'tracing the cosmic expansion to z 1 with type ia supernovae', 'publishedDate': ''}, {'name': 'brian schmidt', 'authorID': '807F639E', 'numpaper': 1, 'affiliation': '', 'field': ['Identification'], 'mostWeightedPaper': 'breaking the code the seven class i railroads use different systems to keep track of their trains and knowing their tricks can yield useful train watching intel', 'publishedDate': '2015/01'}, {'name': 'brian schmidt', 'authorID': '809BE91A', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'doctoral recital 2011 02 24 brian schmidt conductor', 'publishedDate': '2011/02/24'}, {'name': 'brian schmidt', 'authorID': '80AF1724', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'case presentations and review of plexiform schwannoma in the foot', 'publishedDate': '2014/01/03'}, {'name': 'brian p schmidt', 'authorID': '80C73DCD', 'numpaper': 1, 'affiliation': '', 'field': ['Methane'], 'mostWeightedPaper': 'methane rare gas interaction potentials from scattering experiments', 'publishedDate': '1988/10/15'}, {'name': 'brian schmidt', 'authorID': '8137A565', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'looking for unbeamed grbs using the skymappertelescope', 'publishedDate': ''}, {'name': 'brian schmidt', 'authorID': '81879044', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'mooring system for watercraft', 'publishedDate': '2008/06/10'}, {'name': 'brian p schmidt', 'authorID': '81A844AF', 'numpaper': 1, 'affiliation': '', 'field': ['Cation-exchange capacity'], 'mostWeightedPaper': 'passively mode locked multi ghz 1 3 m nd vanadate lasers with low timing jitter', 'publishedDate': ''}, {'name': 'brian p schmidt', 'authorID': '81AB3A05', 'numpaper': 1, 'affiliation': '', 'field': ['Fiber Bragg grating', 'Rate equation', 'Video feedback'], 'mostWeightedPaper': 'dynamics of multimode diode lasers with strong frequency selective optical feedback', 'publishedDate': '2003/09/09'}, {'name': 'brian schmidt', 'authorID': '81AFF994', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'growth factors in oral carcinogenesis', 'publishedDate': '2015/05/07'}, {'name': 'brian schmidt', 'authorID': '81EC1CEF', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'lip cancer clinical presentation biologic behavior and incidence', 'publishedDate': '2012/09/13'}, {'name': 'brian schmidt', 'authorID': '832DEAB2', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'kappa carrageenase and kappa carrageenase containing compositions', 'publishedDate': '2009/02/19'}, {'name': 'brian schmidt', 'authorID': '836073E9', 'numpaper': 1, 'affiliation': 'DepartmentsofNeurologyandNeurosurgery,andRadiology,McGillUniversityandTheMontrealGeneralHospital,Montreal', 'field': [], 'mostWeightedPaper': 'computed tomography in the evaluation of plexopathies and proximal neuropathies', 'publishedDate': '1983/11/01'}, {'name': 'brian schmidt', 'authorID': '83FD3586', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'transseptal catheterization assembly and methods', 'publishedDate': '2007/11/22'}, {'name': 'brian schmidt', 'authorID': '847AB356', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'future directions of clinical care', 'publishedDate': '2013/10/11'}, {'name': 'brian schmidt', 'authorID': '84A1446F', 'numpaper': 1, 'affiliation': '', 'field': ['Information technology'], 'mostWeightedPaper': 'the future of education in an online world', 'publishedDate': '2014/02/28'}, {'name': 'brian p schmidt', 'authorID': '84C69A43', 'numpaper': 1, 'affiliation': 'Resident,DivisionofOralandMaxillofacialSurgery,MetroHealthMedicalCenter,Cleveland,OH', 'field': [], 'mostWeightedPaper': 'hyperparathyroidism jaw tumor syndrome a case report', 'publishedDate': '2009/01/02'}, {'name': 'brian schmidt', 'authorID': '856384C7', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'leader peptides for enhancing secretion of recombinant protein from a host cell', 'publishedDate': '2001/06/05'}, {'name': 'brian schmidt', 'authorID': '85696F3D', 'numpaper': 1, 'affiliation': 'BrianSchmidtStudios,LLC,Bellevue,WA,USA', 'field': [], 'mostWeightedPaper': 'rendering sound and images together', 'publishedDate': '2013/08'}, {'name': 'brian schmidt', 'authorID': '859A961C', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'interactive mixing of game audio', 'publishedDate': '2003/10/01'}, {'name': 'brian schmidt', 'authorID': '85EECF47', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'playing with sound audio hardware and software on xbox', 'publishedDate': '2002/04/01'}, {'name': 'brian paul schmidt', 'authorID': '861F0A51', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'supernova 1998dq in ngc 6754', 'publishedDate': ''}, {'name': 'brian schmidt', 'authorID': '8633EDF3', 'numpaper': 1, 'affiliation': '', 'field': [], 'mostWeightedPaper': 'writing guide for the schmidt lab in conformance with icmje uniform requirements for manuscripts submitted to biomedical journals ama manual of style and essentials of writing biomedical research papers 2 nd edition includes how to use the automatic standardized formatting provided by the ms word template document template_for_manuscripts_schmidt_lab doc', 'publishedDate': ''}]


AuthorList = []
def loadAuthorList():
    global AuthorList
    path = os.path.join(BASE_DIR, "webapp/cache/AuthorList.txt")
    if len(AuthorList) == 0:
        with open(path, "r") as f:
            AuthorList = [name.strip() for name in f]
    AuthorList = list(set(AuthorList))
    return AuthorList

def getFlowerTest(aids):
    inflin = os.path.join(BASE_DIR, "output/flower1.png")
    inflby = os.path.join(BASE_DIR, "output/flower2.png")
    inflflower = [inflin, inflby]
    return inflflower

def main(request):
    optionlist = [  # option list
        {"id":"author", "name":"Author"},
        {"id":"conf", "name":"Conf/Journal"},
        {"id":"inst", "name":"Institution"},
    ]
    keyword = ""
    option = optionlist[0] # default selection
    inflflower = None
    authors = []

    # get user input from main.html page
    if request.method == "GET":
        print(request.GET)
        if "search" in request.GET:
            keyword = request.GET.get("keyword")
            if keyword == "brian schmidt":
                authors, aid_pid_dict =  getAuthor(keyword) #(authors_testing, dict()) # getAuthor(keyword)
            option = [x for x in optionlist if x.get('id', '') == request.GET.get("option")][0]
            print(keyword, option)

            # path to the influence flowers
            inflin = os.path.join(BASE_DIR, "output/flower1.png")
            inflby = os.path.join(BASE_DIR, "output/flower2.png")
            inflflower = []#[inflin, inflby]
        if "submit" in request.GET:
            authorIDs = [auth["authorID"] for auth in authors if auth["authorID"] in request.GET.get("authorList")]
            inflflower = getFlower(authorIDs)
            print("authorIDs: "+str(authorIDs))

    # render page with data
    return render(request, "main.html", {
        "autoCompleteAuthor": loadAuthorList(),
        "optionlist": optionlist,
        "selectedKeyword": keyword,
        "selectedOption": option,
        "inflflower": inflflower,
        "authors": authors
    })
