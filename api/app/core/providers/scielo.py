import logging
import requests

from core.utils import rtd2


logger = logging.getLogger(__name__)
scielo_base = 'http://search.scielo.org/?q='


def scielo(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    logger.info("Searching scielo ...")
    #print("searching scielo")
    hits = {'hits': []}
    count = 0

    if doi:
        q = doi
    else:
        q = author+title+year

    query = scielo_base+q+"&lang=es&count=10&from=0&output=ris&sort=&format=summary&fb=&page=1"
    iface_query = "https://search.scielo.org/?lang=en&count=15&from=0&output=site&sort=&format=summary&fb=&page=1&q="+q

    ris = requests.get(query)
    bris = ris.text.split("ER  -")

    for i in bris[:-1]:
        mdata = rtd2(i)
        mdata['rank'] = count
        mdata['query'] = iface_query
        hits['hits'].append(mdata)
        count += 1

    logger.debug(hits)

    result_queue.put({'scielo': hits})
    return {'scielo': hits}
