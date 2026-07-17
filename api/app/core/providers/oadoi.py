import json
import logging
import requests
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
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
    request_timeout=5,
    oadoi_email="smrkej@coventry.ac.uk"
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


class UnpaywallProvider(Provider):
    def __init__(self, cfg, secrets):
        super().__init__(cfg)
        self.email = secrets["OADOI_EMAIL"]

    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from Unpaywall (oadoi) ...")
        if not self.has_supported_params(request):
            logger.debug("No supported parameters")
            return []
            
        raw_items = self._fetch(request)
        results = []
        logger.debug(type(raw_items))
        # a bit safer if issues
        for item in raw_items:
            try:
                results.append(self.to_bibrecord(item).to_dict())
            except Exception:
                logger.exception("Failed processing item: %r", item)

        logger.debug(
            json.dumps(results, indent=2, default=str)
        )
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        query = self._build_query(request)
        logger.debug(query)

        results = fetch_provider(
            "oadoi",
            query,
            None,
            request_timeout=request.request_timeout,
            format="json"
        )
        logger.debug(
            json.dumps(results, indent=2, default=str)
        )

        if not results:
            return []
        
        return [results] # no hit limit implemented as it only returns one article

    def _build_query(self, request: SearchRequest) -> str:
        params = urlencode({"email": self.email})
        return f"{self.config.query_url}/{request.doi}?{params}"
        # search does not work atm getting 500 from their side
        # params = urlencode({
        #     "query": f"{request.author} {request.title}",
        #     "email": self.email,
        # })

        # return f"{self.config.query_url}search?{params}"