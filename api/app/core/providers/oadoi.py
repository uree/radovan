import logging
import requests


logger = logging.getLogger(__name__)
oadoi_base = 'https://api.unpaywall.org/v2/'


def oadoi(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    global oadoi_email
    email = oadoi_email
    # print("Searching oadoi ...")
    logger.info("Searching oadoi ...")
    hits = {'hits': []}

    if doi:
        query = doi+'?email='+email
        query_url = oadoi_base+query

        request = requests.get(query_url)
        data = request.json()

        data['type'] = 'article'
        data['query'] = oadoi_base
        hits['hits'].append(data)

    result_queue.put({'oadoi': hits})
    return {'oadoi': hits}
