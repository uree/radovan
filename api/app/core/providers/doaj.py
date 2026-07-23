import logging
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
from .utils import fetch_provider

logger = logging.getLogger(__name__)


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
            self.config.code_name,
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
