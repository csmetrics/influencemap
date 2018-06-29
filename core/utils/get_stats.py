

def between(x, a, b):
    # return whether x lies between a and b inclusive
    low = min(a,b)
    high = max(a,b)
    return (x >= low and x <= high)

def get_stats(papers, min_year=None, max_year=None):

    # get min year if not set
    if not min_year:
        min_year = min([paper['Year'] for paper in papers])

    # get max year if not set
    if not max_year:
        max_year = max([paper['Year'] for paper in papers])

    num_years = 1+max_year-min_year
    papers = [paper for paper in papers if (between(paper['Year'], min_year, max_year))]
    num_papers = len(papers)
    avg_papers = round(num_papers/num_years, 1)
    num_refs = sum([len(paper['References']) for paper in papers])
    avg_refs = int(round(num_refs/num_papers,0))
    num_cites = sum([len(paper['Citations']) for paper in papers])
    avg_cites = int(round(num_cites/num_papers,0))

    stats = {
        "min_year": min_year,
        "max_year": max_year,
        "num_papers": num_papers,
        "avg_papers": avg_papers,
        "num_refs": num_refs,
        "avg_refs": avg_refs,
        "num_cites": num_cites,
        "avg_cites": avg_cites,
    }
    return stats

def year_range(papers):
    min_year = min([paper['year'] for paper in papers])
    max_yera = max([paper['year'] for paper in papers])
