import logging
import requests

logger = logging.getLogger(__name__)
doaj_base = 'https://doaj.org/api/v1/search/articles/'


def doaj(result_queue, author='', title='', year='', doi='', isbn='', hit_limit = 10):
    #print("Searching doaj ...")
    logger.info("Searching doaj ...")
    count = 0
    hits = {'hits': []}

    # doi needs to be stripped
    if doi:
        query = 'doi:'+doi
    else:
        query = author+'%20'+str(year)+'%20'+title

    doaj_url = doaj_base+query
    iface_query = "https://doaj.org/search?ref=homepage-box&source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22"+query+"%22%2C%22default_operator%22%3A%22AND%22%7D%7D%7D"

    try:
        request = requests.get(doaj_url, timeout=5)
        logger.debug(f"{request.status_code}")
        data = request.json()
    except Exception as e:
        logger.debug(e)
        result_queue.put({'doaj': hits})
        return hits

    for i in data['results']:
        i['bibjson']['rank'] = count
        i['bibjson']['type'] = 'article'
        i['bibjson']['query'] = iface_query
        count += 1

    hits['hits'] = data['results']
    result_queue.put({'doaj': hits})
    return hits
