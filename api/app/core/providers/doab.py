import logging
import requests

from .utils import fetch_provider

logger = logging.getLogger(__name__)
doab_base = 'https://directory.doabooks.org/rest/search?query='


def doab(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=10,
    request_timeout=5
):

    # can search by ISBN and DOI!
    if len(isbn) > 2:
        query = isbn+'&expand=metadata&limit='+str(hit_limit)
    else:
        query = author+'+'+title+'+'+year+'&expand=metadata,bitstreams&limit='+str(hit_limit)
        # query = author+'+'+title+'+'+year
        query = query.replace(' ', '+')

    doab_url = doab_base+query

    hits = {'hits': []}

    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0"}  # noqa:501

    results = fetch_provider(
        "doab",
        doab_url,
        headers,
        request_timeout=request_timeout,
        format="json"
    )
    if not results:
        result_queue.put({'doab': hits})
        return {'doab': hits}

    # unnest metadata and isolate cover and link url; this is the way
    for i in range(len(results)):
        results[i]['rank'] = i

        try:
            bit_meta = results[i]['bitstreams'][0]['metadata']
        except Exception as e:
            logger.debug(e)
            bit_meta = None

        if bit_meta:
            for b in bit_meta:
                # extract download url
                if b['qualifier'] == 'downloadUrl':
                    results[i]['url'] = b['value']

                    # construct cover url
                    results[i]['coverurl'] = 'https://directory.doabooks.org/bitstream/handle/'+results[i]['handle']+'/'+b['value'].split('/')[-1]+'.jpg'  # noqa:E501

        for m in results[i]['metadata']:
            results[i][m['key']] = m['value']
        del results[i]['metadata']
        del results[i]['bitstreams']
        # confuses bibjson_methods and is a duplicate of dc.title anyway
        del results[i]['name']
        # by default these are /rest links and they take you to an xml page
        results[i]['link'] = 'https://directory.doabooks.org/handle/'+results[i]['handle']

    hits['hits'] = results
    logger.debug(hits)

    result_queue.put({'doab': hits})
    return {'doab': hits}
