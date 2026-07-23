import logging
import requests
from typing import Iterable, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from .base_provider import Provider
from .utils import fetch_provider


logger = logging.getLogger(__name__)


class LibgenProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from Libgen ...")
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
        api_urls = []
        results = []
        query_url = self._build_query(request)
        logger.debug(query_url)

        if request.doi or request.isbn:
            api_urls.append(query_url)
        else:

            html = fetch_provider(
                self.config.code_name,  # TO DO: why keep using this name?
                query_url,
                None,
                request_timeout=request.request_timeout,
                format="text"
            )
        
            # list of urls to fetch json from 
            api_urls = self._parse_html(html)

        logger.debug("This is what we're calling next.")
        logger.debug(api_urls)

        for url in api_urls[:request.hit_limit]:
            item = fetch_provider(
                self.config.code_name,
                url,
                {"Connection": "close"},
                request_timeout=request.request_timeout,
                format="json"
            )
            logger.debug(item)
            normalized = self._normalize_item(item)
            logger.debug(normalized)
            if normalized:
                results.append(normalized)

        return results

    def _build_query(self, request: SearchRequest) -> str:
        if request.doi:
            return f"{self.config.url}/json.php?object=e&doi={request.doi}"
        elif request.isbn:
            return f"{self.config.url}/json.php?object=e&isbn={request.isbn}"
        else:   
            search_terms = " ".join(
                part
                for part in [
                    request.title,
                    request.author,
                    request.year,
                ]
                if part
            )
            return f"{self.config.query_url}?req={quote_plus(search_terms)}&res={request.hit_limit}"

    def _normalize_item(self, result) -> dict | None:
        """In this case add some information to the json object."""
        item = next(iter(result.values()), {})
        file_info = next(iter(item.get("files", {}).values()), {})
        logger.debug(file_info)  # there are multiple files available, sometimes
        md5 = file_info.get("md5", "")
        logger.debug(md5)

        # questionable https://libgen.vg/covers/2427000/e9eb910558caac2cd58a6cad4dcb9cb9.jpg
        libgen_id = item.get("libgen_id", "")
        logger.debug(libgen_id)
        if not item["cover_url"]:
            item["cover_url"] = f"{self.config.url}/covers/{libgen_id[:4] + "000"}.jpg" if libgen_id else ""
        # TO DO: download url does not end up in api response and is not really a download link (= landing url libgen download)
        item["download_url"] = f"{self.config.url}/ads.php?md5={md5}" if md5 else ""
        item["landing_url"] = f"{self.config.url}/file.php?md5={md5}" if md5 else ""

        return item
    
    def _parse_html(self, html: str) -> list:
        """Extract ids from html and return API compatible urls based on said ids."""
        api_urls = []
        soup = BeautifulSoup(html, "lxml")

        get_tags = soup.select('a[href*="edition.php?id"]')

        ids = {
            href.split("id=")[-1]
            for tag in get_tags
            if (href := tag.get("href"))
        }
        # walrtus operator does this
        # href = tag.get("href")
        # if href is not None and href != "":

        api_urls = [
            f"{self.config.url}/json.php?object=e&ids={id_}&fields=*&addkeys=*"
            for id_ in ids
        ]

        return api_urls
