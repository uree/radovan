import logging
import re
from typing import Iterable, List
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from app.core.fixing_links import url_constructor
from .base_provider import Provider
from .utils import fetch_provider


logger = logging.getLogger(__name__)
LIBGEN_HOME = 'https://libgen.vg'
LIBGEN_BASE_ARTICLES = LIBGEN_HOME+"/index.php"


def libgen_article(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=10,
    request_timeout=5
):

    hits = {'hits': []}

    if doi:
        query = 'req='+doi
    else:
        query = 'req='+title+'+'+author

    libgen_url = LIBGEN_BASE_ARTICLES+query

    results = fetch_provider(
        "libgen_article",
        libgen_url,
        None,
        request_timeout=request_timeout,
        format="text"
    )
    if not results:
        result_queue.put({'libgen_article': hits})
        return {'libgen_article': hits}

    soup = BeautifulSoup(results, 'lxml')
    rows = soup.select(".catalog > tbody > tr")

    for i in rows[:hit_limit]:
        item = {}
        journal = {'name': '', 'volume': '', 'issue': '', 'year':''}

        tds = i.select('td')
        try:
            auth_data = tds[0].get_text().split(';')
        except Exception as e:
            logger.debug(e)
            auth_data = tds[0].get_text()

        # check for impurities
        item['landing_url'] = LIBGEN_HOME+'/'+tds[1].a.get('href')

        get_doi = tds[1].a.get('href').split("scimag/")[-1]
        get_title = tds[1].a.get_text()

        try:
            journal_data = tds[2].select('p')
            journal['name'] = journal_data[0].get_text()
            journal_info = re.findall(r'\d+', journal_data[1].get_text())
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)
        try:
            journal['volume'] = journal_info[0]
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)
        try:
            journal['issue'] = journal_info[1]
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)
        try:
            journal['year'] = journal_info[2]
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)

        links = tds[4].select('a')

        item['href'] = [url_constructor(l.get_text(), l.get_text(), l.get('href')) for l in links]  # noqa
        item['query'] = libgen_url
        item['author'] = auth_data
        item['doi'] = get_doi
        item['title'] = get_title
        item['journal'] = journal
        hits['hits'].append(item)

    result_queue.put({'libgen_article': hits})
    return {'libgen_article': hits}



class LibgenArticleProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from Libgen Articles ...")
        raw_items = self._fetch(request)

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]

        logger.debug(results)
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        query = self._build_query(request)
        libgen_url = LIBGEN_BASE_ARTICLES + query

        results = fetch_provider(
            "libgen_article",
            libgen_url,
            None,
            request_timeout=request.request_timeout,
            format="text"
        )

        if not results:
            return []

        soup = BeautifulSoup(results, 'lxml')
        # logger.debug(soup)
        rows = soup.select("#tablelibgen > tbody > tr")
        logger.debug(rows)
        results = []

        for row in rows[:request.hit_limit]:
            normalized = self._normalize_item(row, libgen_url)

            if normalized:
                results.append(normalized)
        return results

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

        return f"?req={quote_plus(search_terms)}&res={request.hit_limit}"

    def _normalize_item(self, item, query: str) -> dict | None:
        tds = item.select('td')
        if len(tds) < 5:
            return None

        try:
            first_td = tds[0]

            # Journal
            journal_link = first_td.select_one("a[href*='series.php']")
            journal_name = journal_link.get_text(strip=True) if journal_link else ""

            # Landing page
            edition_link = first_td.select_one("a[href*='edition.php']")
            if not edition_link:
                return None

            landing_href = edition_link.get("href")

            # Volume / issue from:
            # "2010-aug 04 vol. 28 iss. 19"
            edition_text = edition_link.get_text(" ", strip=True)

            volume_match = re.search(r"vol\.\s*(\d+)", edition_text, re.I)
            issue_match = re.search(r"iss\.\s*(\d+)", edition_text, re.I)

            # Title
            title_link = first_td.select("a[href*='edition.php']")
            title = ""
            if len(title_link) >= 2:
                title = title_link[1].get_text(strip=True)

            # DOI
            doi_match = re.search(
                r"DOI:\s*([^\s<]+)",
                first_td.get_text(" ", strip=True),
                re.I,
            )
            doi = doi_match.group(1) if doi_match else ""

            # Authors
            authors = [
                author.strip()
                for author in tds[1].get_text(strip=True).split(";")
                if author.strip()
            ]

            # Date
            year = ""
            date_text = tds[3].get_text(" ", strip=True)

            year_match = re.search(r"\b(\d{4})\b", date_text)
            if year_match:
                year = year_match.group(1)

            journal = {
                "name": journal_name,
                "volume": volume_match.group(1) if volume_match else "",
                "issue": issue_match.group(1) if issue_match else "",
                "year": year,
            }

            # Download / mirror links
            links = tds[8].select("a")

            return {
                "landing_url": self._absolute_url(landing_href),
                "href": [
                    url_constructor(
                        link.get("title", link.get_text(strip=True)),
                        link.get_text(strip=True),
                        self._absolute_url(link.get("href")),
                    )
                    for link in links
                    if link.get("href")
                ],
                "query": query,
                "author": authors,
                "doi": doi,
                "title": title,
                "journal": journal,
                "type": "article",
            }

        except Exception as e:
            logger.debug(f"Error normalizing article row: {e}")
            return None

    def _absolute_url(self, url: str) -> str:
        if url.startswith('http'):
            return url

        if url.startswith('../'):
            return f"{LIBGEN_HOME}/{url[3:]}"

        return f"{LIBGEN_HOME}/{url.lstrip('/')}"
