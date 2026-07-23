import json
import logging
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
from .utils import fetch_provider


logger = logging.getLogger(__name__)


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
            self.config.code_name,
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