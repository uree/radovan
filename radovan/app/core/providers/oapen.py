import logging
from collections.abc import Iterable
from urllib.parse import quote_plus

from app.api.v2_0.request import SearchRequest

from .base_provider import Provider, ProviderResults
from .utils import fetch_provider

logger = logging.getLogger(__name__)
OAPEN_HANDLE_BASE = "https://library.oapen.org/handle"
OAPEN_BITSTREAM_BASE = "https://library.oapen.org/bitstream/handle"


class OAPENProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[ProviderResults]:
        logger.debug("Fetching from OAPEN ...")
        if not self.has_supported_params(request):
            logger.debug("No supported parameters")
            return []
            
        raw_items, query = self._fetch(request)

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]

        logger.debug(results)
        return ProviderResults(items=results, query=query)

    def _fetch(self, request: SearchRequest) -> list[dict]:
        query = self._build_query(request)

        headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0"}  # noqa:501

        results = fetch_provider(
            self.config.code_name,
            query,
            headers,
            request_timeout=request.request_timeout,
            format="json"
        )
        logger.debug(results)

        if not results:
            return []

        normalized = [
            self._normalize_item(item)
            for item in results[:request.hit_limit]
        ]
        return normalized, query

    def _build_query(self, request: SearchRequest) -> str:
        if request.isbn:
            search_terms = request.isbn
        elif request.doi:
            search_terms = request.doi
        else:
            search_terms = " ".join(
                part
                for part in [
                    request.author,
                    request.title,
                    request.year,
                ]
                if part
            )

        return (
            f"{self.config.query_url}"
            f"{quote_plus(search_terms)}"
            f"&expand={quote_plus('metadata,bitstreams')}"
            f"&limit={request.hit_limit}"
        )

    def _normalize_item(self, item: dict) -> dict:
        normalized = {
            key: value
            for key, value in item.items()
            if key not in {"metadata", "bitstreams", "name"}
        }

        handle = item.get("handle")
        if handle:
            normalized["link"] = f"{OAPEN_HANDLE_BASE}/{handle}"

        for metadata in item.get("metadata", []):
            key = metadata.get("key")
            value = metadata.get("value")
            if key and value:
                normalized[key] = value

        for bitstream in item.get("bitstreams", []):
            bitstream_name = bitstream.get("name")

            if handle and bitstream_name:
                bitstream_url = f"{OAPEN_BITSTREAM_BASE}/{handle}/{bitstream_name}"
                normalized["standard_oapen_url"] = bitstream_url
                normalized["coverurl"] = f"{bitstream_url}.jpg"

            for metadata in bitstream.get("metadata", []):
                if metadata.get("key") != "dc.identifier.uri":
                    continue

                download_url = metadata.get("value")
                if download_url:
                    normalized["url"] = download_url

            return normalized

        return normalized
