import logging
from typing import Iterable  # noqa: UP035
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from app.api.v2_0.request import SearchRequest

from .base_provider import Provider, ProviderResults

logger = logging.getLogger(__name__)


class LibgenProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[ProviderResults]:
        logger.debug("Fetching from Libgen ...")
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

    def _fetch(self, request: SearchRequest) -> tuple:
        results = []
        query_url = self._build_query(request)
        logger.debug(query_url)

        with sync_playwright() as p:
            try:
                browser = p.firefox.launch(headless=True)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:151.0) "
                        "Gecko/20100101 Firefox/151.0"
                    )
                )
                page.goto(query_url, wait_until="networkidle")
                html = page.content()
                # logger.debug(html)
                browser.close()
            except Exception as e:  # noqa: BLE001
                logger.debug(e)
        
        results = self._parse_html(html, self.config.url)
        # logger.debug(json.dumps(results, indent=2))

        return results, query_url

    def _build_query(self, request: SearchRequest) -> str:
        if request.doi:
            search_terms = request.doi
        elif request.isbn:
            search_terms = request.isbn
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

    def _normalize_item(self, result):
        ...

    def _parse_html(self, html: str, base_url: str = "") -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        records = []
        
        # First row contains pagination
        for row in soup.select("#tablelibgen tbody tr"):
            # When making a DOI query ...the first cell is in the way
            cells = [
                cell
                for cell in row.find_all("td", recursive=False)
                if not cell.has_attr("bgcolor")
            ]
            logger.debug(cells)

            def get_cell(index):
                return cells[index] if index < len(cells) else None  # noqa: B023

            def cell_text(index):
                cell = get_cell(index)
                return cell.get_text(" ", strip=True) if cell else ""

            # Extract the title from the edition link.
            title = ""
            edition_link = None
            first_cell = get_cell(0)

            # The first cell is a bit messy
            if first_cell:
                for link in first_cell.find_all("a", href=True):
                    if "edition.php" in link["href"]:
                        text = link.get_text(" ", strip=True)
                        edition_link = link.get("href")

                        if text and not text.startswith("DOI:"):
                            title = text
                            if not any(char.isdigit() for char in text) or len(text) > 20:
                                break

            edition_links = (
                first_cell.select('a[href*="edition.php"]')
                if first_cell
                else []
            )
            candidates = [
                a.get_text(" ", strip=True)
                for a in edition_links
                if a.get_text(" ", strip=True)
                and not a.get_text(" ", strip=True).startswith("DOI:")
            ]

            if candidates:
                title = candidates[1] if len(candidates) > 1 else candidates[0]

            author = cell_text(1)
            publisher = cell_text(2)

            year_text = cell_text(3)
            year = year_text[:4] if year_text[:4].isdigit() else ""

            language = cell_text(4)
            ext = cell_text(7)
            size = cell_text(6)

            mirrors_cell = get_cell(8)
            mirrors = []

            if mirrors_cell:
                for link in mirrors_cell.find_all("a", href=True):
                    name = link.get_text(" ", strip=True)
                    href = link["href"]
                    if href.startswith("/"):
                        logger.debug(href)
                    if href.startswith(("/ads.php", "/index.php", "/get.php")):
                        href = urljoin(base_url, href)

                    mirrors.append({
                        "name": name,
                        "type": "landing_url",
                        "href": href,
                    })

            if edition_link:
                edition_link = urljoin(base_url, edition_link)
                mirrors.append({
                    "name": "",
                    "type": "landing_url",
                    "href": edition_link,
                })


            records.append({
                "title": title,
                "author": author,
                "publisher": publisher,
                "year": year,
                "language": language,
                "ext": ext,
                "size": size,
                "links": mirrors,
            })

        return records
