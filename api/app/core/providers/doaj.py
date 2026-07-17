import logging
import requests
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
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


class DOAJProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from DOAJ ...")
        if not self.has_supported_params(request):
            logger.debug("No supported parameters")
            return []
            
        raw_items = self._fetch(request)
        results = []
        # a bit safer if issues
        for item in raw_items:
            try:
                results.append(self.to_bibrecord(item).to_dict())
            except Exception:
                logger.exception("Failed processing item: %r", item)

        logger.debug(results)
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        query = self._build_query(request)
        logger.debug(query)

        results = fetch_provider(
            "doaj",
            query,
            None,
            request_timeout=request.request_timeout,
            format="json"
        )
        logger.debug(results)

        if not results:
            return []
        
        return results["results"][:request.hit_limit]

    def _build_query(self, request: SearchRequest) -> str:
        if request.doi:
            search_query = f"doi:{request.doi}"
        else:
            search_query = " AND ".join(
                part
                for part in (
                    f"bibjson.author.name:{request.author}" if request.author else None,
                    f"title:{request.title}" if request.title else None,
                    f"bibjson.year:{request.year}" if request.year else None,
                )
                if part
            )

        params = {
            "page": 0,
            "pageSize": request.hit_limit,
        }
        return f"{self.config.query_url}{search_query}?{urlencode(params)}"
