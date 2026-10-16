import logging
from collections.abc import Iterable

import requests

from app.api.v2_0.request import SearchRequest

from .base_provider import Provider, ProviderResults

logger = logging.getLogger(__name__)


class MOTWProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[ProviderResults]:
        logger.debug("Fetching from memoryoftheworld ...")
        if not self.has_supported_params(request):
            logger.debug("No supported parameters")
            return []
        
        raw_items, query = self._fetch(request)
        # consider this: return results meta like count

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]

        logger.debug(results)
        return ProviderResults(items=results, query=query)

    def _fetch(self, request: SearchRequest) -> tuple:
        query = self._build_query(request)
        logger.debug(query)

        try:
            r = requests.get(query, verify=False, timeout=request.request_timeout) # ssl
            results = r.json()["_items"]
        except requests.exceptions.SSLError:
            return [], query
        except Exception as e:  # noqa: BLE001
            logger.debug(e)
            return [], query

        normalized = [
            self._normalize_item(item)
            for item in results[:request.hit_limit]
        ]
        return normalized, query

    def _build_query(self, request: SearchRequest) -> str:
        url_authors = "https://library.memoryoftheworld.org/search/authors/"
        url_title = "https://library.memoryoftheworld.org/search/title/"
        
        if request.author and request.title:
            return f"{url_title}{request.title}"

        if request.author:
            return f"{url_authors}{request.author}"

        if request.title:
            return f"{url_title}{request.title}"

    def _normalize_item(self, item: dict) -> dict:
        output = {}

        url_base = f"{self.config.url}{item['library_url']}"
        linksos = []

        for f in item["formats"]:
            try:
                href = f"{url_base}{f['dir_path']}{f['file_name']}"
                text = f["format"]

                linksos.append({
                    "href": href,
                    "format": text.lower()
                })

            except Exception as e:  # noqa: BLE001
                logger.debug(e)
                continue

        output["author"] = [n for n in item["authors"]]
        output["title"] = item["title"]
        output["href"] = linksos
        output["type"] = "book"
        output["img_href"] = f"{url_base}{item['cover_url']}"

        return output

