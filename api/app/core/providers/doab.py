import logging
from typing import Iterable, List
from urllib.parse import quote_plus

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
from .utils import fetch_provider

logger = logging.getLogger(__name__)
DOAB_HANDLE_BASE = "https://directory.doabooks.org/handle"
DOAB_BITSTREAM_BASE = "https://directory.doabooks.org/bitstream/handle"


class DOABProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from DOAB ...")
        if not self.has_supported_params(request):
            logger.debug("No supported parameters")
            return []

        raw_items = self._fetch(request)

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]

        logger.debug(results)
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        logger.debug("Fetch called.")
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

        return [
            self._normalize_item(item)
            for item in results[:request.hit_limit]
        ]

    def _build_query(self, request: SearchRequest) -> str:
        if request.isbn:
            search_terms = request.isbn
            expand = "metadata"
        elif request.doi:
            search_terms = request.doi
            expand = "metadata,bitstreams"
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
            expand = "metadata,bitstreams"

        return (
            f"{self.config.query_url}"
            f"{quote_plus(search_terms)}"
            f"&expand={quote_plus(expand)}"
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
            normalized["link"] = f"{DOAB_HANDLE_BASE}/{handle}"

        for metadata in item.get("metadata", []):
            key = metadata.get("key")
            value = metadata.get("value")
            if key and value:
                normalized[key] = value

        for bitstream in item.get("bitstreams", []):
            for metadata in bitstream.get("metadata", []):
                if metadata.get("qualifier") != "downloadUrl":
                    continue

                download_url = metadata.get("value")
                if not download_url:
                    continue

                normalized["url"] = download_url

                if handle:
                    filename = download_url.rsplit("/", 1)[-1]
                    normalized["coverurl"] = (
                        f"{DOAB_BITSTREAM_BASE}/{handle}/{filename}.jpg"
                    )

                return normalized

        return normalized


