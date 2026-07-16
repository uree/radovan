import logging
from typing import Iterable, List
from urllib.parse import urlencode, urljoin, parse_qs


from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider

logger = logging.getLogger(__name__)

# TO DO: continue here ... write test, run some more queries, rename file
class FIDMediaProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from FIDMedia ...")
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

        with sync_playwright() as p:
            try:
                browser = p.firefox.launch(headless=True)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:151.0) "
                        "Gecko/20100101 Firefox/151.0"
                    )
                )
                page.goto(query, wait_until="networkidle")
                html = page.content()
                browser.close()
            except Exception as e:
                logger.debug(e)
        
        logger.debug(html)
        return self._parse_results(html, request.hit_limit)


    def _build_query(self, request: SearchRequest) -> str:
        lookfor = []
        types = []

        if request.title:
            lookfor.append(request.title)
            types.append("AllFields")

        if request.author:
            lookfor.append(request.author)
            types.append("Author")

        if request.year:
            lookfor.append(str(request.year))
            types.append("year")

        if request.isbn:
            lookfor.append(request.isbn)
            types.append("ISN")  # This is what the endpoint appears to expect.

        params = [
            ("join", "AND"),
        ]

        for value in lookfor:
            params.append(("lookfor0[]", value))

        for value in types:
            params.append(("type0[]", value))

        # One AND between each pair of search terms.
        for _ in range(max(0, len(lookfor) - 1)):
            params.append(("bool0[]", "AND"))

        # here i only query open access and online materials, but now that i am only scraping landing urls, this makes less sense, could expand
        params.extend(
            [
                ("limit", request.hit_limit),
                ("filter[]", '~facet_avail:"Online"'), 
                ("filter[]", '~facet_avail:"Free"'),
                ("daterange[]", "publishDateSort"),
                ("publishDateSortfrom", ""),
                ("publishDateSortto", ""),
            ]
        )

        return f"{self.config.query_url}?{urlencode(params)}"
    

    def _parse_results(self, html: str, hit_limit: int) -> dict:
        soup = BeautifulSoup(html, "html.parser")

        results = []

        result_list = soup.select_one("ol")
        logger.debug(result_list)
        if not result_list:
            return results

        for item in result_list.find_all("li", class_="result", recursive=False)[:hit_limit]:
            results.append(self._normalize_item(item))

        return results

    # COinS (ContextObjects in Spans) is a small but clever convention for embedding bibliographic metadata inside HTML pages so that reference managers, library tools, and citation software can extract it.
    def _parse_coins(self, item: str) -> dict:
        span = item.select_one("span.Z3988")

        if not span:
            return {}

        data = parse_qs(span["title"])
        logger.debug("Debugging parse coins.")
        logger.debug(type(data))
        logger.debug(data.keys())
        logger.debug(data)

        return {
            "title": self._first(
                data.get("rft.title")
            ),
            "author": data.get("rft.au", []),
            "year": self._extract_year(self._first(data.get("rft.date"))),
            "publisher": self._first(data.get("rft.pub")),
            "isbn": self._first(data.get("rft.isbn")),
        }

    def _extract_year(self, value: str | None) -> int | None:
        if not value:
            return None

        value = value.strip("[]")

        if value.isdigit():
            return int(value)

        return None


    def _first(self, value):
        return value[0] if isinstance(value, list) and value else value


    def _normalize_item(self, item: dict) -> dict:
        result_body = item.select_one(".result-body")

        title_link = result_body.select_one("a.title")
        logger.debug(title_link)

        url = (
            urljoin(self.config.url, title_link["href"])
            if title_link
            else None
        )

        visible_authors = [
            a.get_text(" ", strip=True)
            for a in result_body.select("a.result-author")
        ]

        coins = self._parse_coins(item)
        logger.debug(coins)

        return {
            "title": coins.get("title"),
            "author": visible_authors or coins.get("author", []),
            "link": url,  # TO DO: this fails
            "landing_url": url,
            "year": coins.get("date"),
            "publisher": coins.get("pub"),
            "isbn": coins.get("isbn"),
        }
