import logging
import requests

from .utils import fetch_provider

logger = logging.getLogger(__name__)
doaj_base = 'https://doaj.org/api/v1/search/articles/'


def doaj(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=10,
    request_timeout=5
):

    count = 0
    hits = {'hits': []}

    # doi needs to be stripped
    if doi:
        query = 'doi:'+doi
    else:
        query = author+'%20'+str(year)+'%20'+title

    doaj_url = doaj_base+query
    iface_query = "https://doaj.org/search?ref=homepage-box&source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22"+query+"%22%2C%22default_operator%22%3A%22AND%22%7D%7D%7D"  # noqa:501

    results = fetch_provider(
        "doaj",
        doaj_url,
        None,
        request_timeout=request_timeout,
        format="json"
    )
    if not results:
        result_queue.put({'doaj': hits})
        return hits

    for i in results['results']:
        i['bibjson']['rank'] = count
        i['bibjson']['type'] = 'article'
        i['bibjson']['query'] = iface_query
        count += 1

    hits['hits'] = results['results']
    result_queue.put({'doaj': hits})
    return hits
