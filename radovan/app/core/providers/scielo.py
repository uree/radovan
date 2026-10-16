import logging
from typing import Iterable, List  # noqa
from urllib.parse import urlencode

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.api.v2_0.request import SearchRequest

from .base_provider import Provider, ProviderResults

logger = logging.getLogger(__name__)

# supposed api, not documented
# https://articlemeta.scielo.org/api/v1/
# useless docs: https://scielo.readthedocs.io/en/latest/
# useful repo: https://github.com/scieloorg/articles_meta/issues?
# documentation in .rst files in the articles_meta repo: https://github.com/scieloorg/articles_meta/blob/ddcbd2faf8a4edc04ce4f7d24d9f8df37ea3e6fe/docs/source/api/article.rst#L50
# can query article, collection, issue, journal
# possible formats here https://github.com/scieloorg/search-journals/blob/757b8e1fbf18a93b379364801e506927e1081ff2/iahx/views/search.php#L408
# json blocked, others possibly too
# turns out it's probably easiest to just parse html data, once you fetch the search results with playwright

class ScieloProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[ProviderResults]:
        logger.debug("Fetching from Scielo ...")
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

    # TO DO: figure out a different way. scielo now has bot protection
    def _fetch(self, request: SearchRequest) -> tuple:
        query = self._build_query(request)
        logger.debug(query)

        # fetch search html
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
            except Exception as e:  # noqa: BLE001
                logger.debug(e)
        
        # parse results
        return self._parse_results(html, request.hit_limit), query


    def _build_query(self, request: SearchRequest) -> str:
        if request.doi:
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
        
        params = {
            "q": search_terms,
            "count": request.hit_limit,
            "page": 1,
            "from": 0,
            "output": "site",
            "format": "summary"
        }
        return f"{self.config.query_url}?{urlencode(params)}"

    def _parse_results(self, html: str, hit_limit: int) -> dict:
        soup = BeautifulSoup(html, "lxml")
        results_html = soup.select_one("#ResultArea .results")
        results = []

        try:
            results = [
                self._normalize_item(div)
                for div in results_html.find_all("div", recursive=False)[:hit_limit]
                if div.has_attr("id")
            ]
            logger.debug(results)
        except Exception as e:  # noqa: BLE001
            logger.debug(e)
        
        return results


    def _normalize_item(self, result: dict) -> dict:
        data = {
            "title": None,
            "creators": [],
            "doi": None,
            "journal": None,
            "issn": None,
            "year": None,
            "volume": None,
            "issue": None,
            "pages": None,
            "open_url": [],
            "download_url": [],
        }

        # title + article URL
        title_link = result.select_one("strong.title")
        if title_link:
            data["title"] = title_link.get_text(strip=True)

        article_link = result.select_one("strong.title")
        if article_link and article_link.parent.name == "a":
            data["url"] = article_link.parent["href"]

        # authors
        for a in result.select(".line.authors a.author"):
            data["creators"].append(a.get_text(" ", strip=True))

        # DOI
        doi_elem = result.select_one("[data-doi]")
        if doi_elem:
            data["doi"] = doi_elem.get("data-doi")

        # journal metadata
        source = result.select_one(".line.source")

        if source:
            journal = source.select_one(".dropdown-toggle")
            if journal:
                data["journal"] = journal.get_text(" ", strip=True)

            info = source.select_one(".openJournalInfo")
            if info:
                data["issn"] = info.get("data-issn")

            text = source.get_text(" ", strip=True)

            # crude but works for this structure
            import re

            m = re.search(r"(\d{4})", text)
            if m:
                data["year"] = m.group(1)

            m = re.search(r"Volume\s+(\d+)", text)
            if m:
                data["volume"] = m.group(1)

            m = re.search(r"N[ºo]\s+(\d+)", text)
            if m:
                data["issue"] = m.group(1)

            m = re.search(r"Páginas\s+(\d+\s*-\s*\d+)", text)
            if m:
                data["pages"] = m.group(1)

        # Texto links
        # TO DO: how do i parse these
        versions = result.select_one(".line.versions")

        if versions:
            for link in versions.select('a[href*="sci_arttext"]'):
                # lang = link.get_text(strip=True).lower()
                # data["texto"][lang] = link["href"]
                data["open_url"].append(link["href"])

            for link in versions.select('a[href*="sci_pdf"]'):
                # lang = link.get_text(strip=True).lower()
                # data["pdf"][lang] = link["href"]
                data["download_url"].append(link["href"])

        return data
