import logging
import requests

from core.keys import oadoi_email
from .utils import fetch_provider


logger = logging.getLogger(__name__)
oadoi_base = 'https://api.unpaywall.org/v2/'


def oadoi(
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
        query = doi+'?email='+oadoi_email
    else:
        query = f"search?query={author.strip()} {title.strip()}&email={oadoi_email}"

    query_url = oadoi_base+query

    results = fetch_provider(
        "oadoi",
        query_url,
        None,
        request_timeout=request_timeout,
        format="json"
    )

    if not results:
        result_queue.put({'oadoi': hits})
        return {'oadoi': hits}

    logger.debug(results)

    if doi:
        results['rank'] = 0
        results['type'] = 'article'
        results['query'] = oadoi_base
        logger.debug(results.keys())
        hits['hits'].append(results)
    else:
        for r in results["results"][:hit_limit]:
            res = r["response"]
            res['type'] = 'article'
            res['query'] = oadoi_base
            res['rank'] = count
            logger.debug(res.keys())
            hits['hits'].append(res)
            count += 1

    logger.debug(hits)

    result_queue.put({'oadoi': hits})
    return {'oadoi': hits}
