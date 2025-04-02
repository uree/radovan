import logging

from core.utils import rtd2
from .utils import fetch_provider

logger = logging.getLogger(__name__)
scielo_base = 'http://search.scielo.org/?q='


def scielo(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=10,
    request_timeout=5
):
    hits = {'hits': []}
    count = 0

    if doi:
        q = doi
    else:
        q = author+title+year

    query = scielo_base+q+"&lang=es&count=10&from=0&output=ris&sort=&format=summary&fb=&page=1"
    iface_query = "https://search.scielo.org/?lang=en&count=15&from=0&output=site&sort=&format=summary&fb=&page=1&q="+q

    results = fetch_provider(
        "scielo",
        query,
        None,
        request_timeout=request_timeout,
        format="text"
    )

    if not results:
        result_queue.put({'scielo': hits})
        return {'scielo': hits}

    bris = results.split("ER  -")

    for i in bris[:-1]:
        mdata = rtd2(i)
        mdata['rank'] = count
        mdata['query'] = iface_query
        hits['hits'].append(mdata)
        count += 1

    logger.debug(hits)

    result_queue.put({'scielo': hits})
    return {'scielo': hits}
