import logging

from .utils import fetch_provider

logger = logging.getLogger(__name__)
oapen_base = 'https://library.oapen.org/rest/search?query='


def oapen(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=3,
    request_timeout=5
):

    if len(isbn) > 2:
        query = isbn+'&expand=metadata,bitstreams'+'&limit='+str(hit_limit)
    elif len(doi) > 2:
        query = doi+'&expand=metadata,bitstreams'+'&limit='+str(hit_limit)
    else:
        query = author+title+year+'&expand=metadata,bitstreams'+'&limit='+str(hit_limit)

    oapen_url = oapen_base+query

    hits = {'hits': []}

    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0"}  # noqa:501

    results = fetch_provider(
        "oapen",
        oapen_url,
        headers,
        request_timeout=request_timeout,
        format="json"
    )

    if not results:
        result_queue.put({'oapen': hits})
        return {'oapen': hits}

    for i in range(len(results)):
        results[i]['rank'] = i
        # there are multiple bitstreams (images, multiple text formats); only using one for now
        try:
            bit = results[i]['bitstreams'][0]
        except:
            bit = None
        try:
            bit_meta = results[i]['bitstreams'][0]['metatada']
        except:
            bit_meta = None

        if bit_meta:
            for b in bit_meta:
                # extract download url
                if b['key'] == 'dc.identifier.uri':
                    results[i]['url'] = b['value']

        if bit:
            results[i]['standard_oapen_url'] = 'https://library.oapen.org/bitstream/handle/'+results[i]['handle']+'/'+bit['name']  # noqa:501

            results[i]['coverurl'] = 'https://library.oapen.org/bitstream/handle/'+results[i]['handle']+'/'+bit['name']+'.jpg'  # noqa:501

        for m in results[i]['metadata']:
            results[i][m['key']] = m['value']

        del results[i]['metadata']
        del results[i]['bitstreams']
        # confuses bibjson_methods and is a duplicate of dc.title anyway
        del results[i]['name']
        # by default these are /rest links and they take you to an xml page
        results[i]['link'] = 'https://library.oapen.org/handle/'+results[i]['handle']

    hits['hits'] = results[:3]
    logger.debug(hits)

    result_queue.put({'oapen': hits})
    return {'oapen': hits}
