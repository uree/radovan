import logging
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
from .utils import fetch_provider

logger = logging.getLogger(__name__)


class OSFProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from OSF ...")
        if not self.has_supported_params(request):
            logger.debug("No supported parameters")
            return []
        
        raw_items = self._fetch(request)
        results = []
        # a bit safer if issues
        for item in raw_items:
            try:
                logger.debug(item)
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
            {"Content-Type": "application/json"},
            request_timeout=request.request_timeout,
            format="json"
        )
        logger.debug(results)

        if not results:
            return []
        # normalize if need be
        try:
            return [
                self._normalize_item(item)
                for item in results["hits"]["hits"][:request.hit_limit]
            ]
        except Exception as e:
            logger.debug(e)
            return []

    def _build_query(self, request: SearchRequest) -> str:
        search_query = " ".join(
            part
            for part in (
                f"contributors:{request.author}" if request.author else None,
                f"title:{request.title}" if request.title else None,
                f"year:{request.year}" if request.year else None,
            )
            if part
        )

        params = {
            "q": search_query,
            "size": request.hit_limit,
        }
        return f"{self.config.query_url}?{urlencode(params)}"
    # TO DO: works for now, revisit when refactoring bibjson_methods
    def _normalize_item(self, item: dict) -> dict:
        normalized = item["_source"].copy()

        identifiers = normalized.get("identifiers")
        if identifiers:
            identifier = identifiers[0]
            normalized["landing_url"] = identifier
            normalized["doi"] = identifier
        else:
            logger.debug("No identifiers found")

        date = normalized.get("date")
        if isinstance(date, str) and len(date) >= 4:
            normalized["year"] = date[:4]
        else:
            logger.debug("Could not derive year from date: %r", date)

        return normalized