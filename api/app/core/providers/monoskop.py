import logging
import re
from typing import Iterable, List
from urllib.parse import quote_plus

import isbnlib
import urllib.request
from bs4 import BeautifulSoup

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from app.core.fixing_links import url_constructor
from .base_provider import Provider


logger = logging.getLogger(__name__)
MONOSKOP_BASE = 'https://monoskop.org/log/?cat=17&s='


class MonoskopProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from Monoskop ...")
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
        monoskop_url = self.config.query_url + self._build_query(request)
        logger.debug(f"Making request {monoskop_url}")

        provider_request = urllib.request.Request(
            monoskop_url,
            headers={"User-Agent": "Magic Browser"}
        )

        try:
            response = urllib.request.urlopen(
                provider_request,
                timeout=request.request_timeout
            )
        except Exception as e:
            logger.debug(e)
            return []

        soup = BeautifulSoup(response, 'lxml')
        items = soup.select(".item")

        results = []
        for item in items[:request.hit_limit]:
            normalized = self._normalize_item(item, monoskop_url)
            if normalized:
                results.append(normalized)

        return results

    def _build_query(self, request: SearchRequest) -> str:
        if request.isbn:
            return quote_plus(request.isbn)

        search_terms = " ".join(
            part
            for part in [
                request.author,
                request.title,
                request.year,
            ]
            if part
        )

        return quote_plus(search_terms)

    def _normalize_item(self, item, query: str) -> dict | None:
        try:
            title = item.select('h1')[0].get_text()
            landing = item.select('h1 a')[0].get('href')
            image = item.select('img')[0]
        except IndexError as e:
            logger.debug(e)
            return None

        img_href = self._absolute_url(image.get('src', ''))
        links, description_parts = self._extract_links_and_description(image)
        logger.debug(item)

        if landing:
            links.append(
                url_constructor(
                    'landing',
                    'landing_url',
                    self._absolute_url(landing)
                )
            )

        return {
            'img_href': img_href,
            'desc': '\n'.join(description_parts),
            'href': links,
            'title': title,
            'query': query,
            'isbn': self._extract_isbns(item),
            'type': 'book',
        }

    def _extract_links_and_description(self, image) -> tuple[list[dict], list[str]]:
        links = []
        description_parts = []

        # This relies on the cover image position in Monoskop's item markup.
        for sibling in image.parent.next_siblings:
            try:
                anchors = sibling.find_all('a')
            except AttributeError:
                continue

            if not anchors:
                text = sibling.get_text(strip=True)
                if text:
                    description_parts.append(text)
                continue

            for anchor in anchors:
                if anchor.text.startswith('Comment'):
                    continue

                href = anchor.get('href')
                if not href:
                    continue

                links.append({
                    'type': anchor.text,
                    'name': anchor.text,
                    'href': self._absolute_url(href),
                })

        return links, description_parts

    # TO DO: is this func reusable elsewhere?
    def _extract_isbns(self, item) -> list[str]:
        return isbnlib.get_canonical_isbn(str(item))

    def _absolute_url(self, url: str) -> str:
        if url.startswith('../'):
            return self.config.url + url[3:]

        if url.startswith('/'):
            return self.config.url.rstrip('/') + url

        return url
