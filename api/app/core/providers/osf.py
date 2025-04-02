import logging

from fixing_links import url_constructor
from .utils import fetch_provider

logger = logging.getLogger(__name__)
osf_base = 'https://share.osf.io/api/v2/search/creativeworks/_search'


def osf(
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

    if doi:
        query = '?q='+doi+'&type=preprint'
    else:
        if len(author) > 1:
            part2 = 'contributors:'+author
        else:
            part2 = ''

        if len(title) > 1:
            part3 = 'title:'+title
        else:
            part3 = ''

        if len(year) > 1:
            part4 = 'year:'+year
        else:
            part4 = ''

        query = '?size='+str(hit_limit)+'&q='+part2+part3+part4

    osf_url = osf_base+query
    headers = {'Content-Type': 'application/json'}

    results = fetch_provider(
        "osf",
        osf_url,
        headers,
        request_timeout=request_timeout,
        format="json"
    )
    logger.debug(results)

    if not results:
        result_queue.put({'osf': hits})
        return {'osf': hits}

    for i in results['hits']['hits']:
        i['_source']['rank'] = count
        i['_source']['landing_url'] = 'https://share.osf.io/preprint/'+i['_id']
        i['_source']['query'] = osf_url
        try:
            ls = []
            ls.append(url_constructor('landing', 'landing_url', i['_source']['identifiers'][0]))
            i['_source']['links'] = ls
        except Exception as e:
            logger.debug('Issue with parsing data in osf(): ', e)
            pass

        count += 1
        hits['hits'].append(i['_source'])

    result_queue.put({'osf': hits})
    return {'osf': hits}
