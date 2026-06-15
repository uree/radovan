import logging
import re
import requests
from typing import Iterable, List
from urllib.parse import urlencode

from concurrent.futures import as_completed
from bs4 import BeautifulSoup, SoupStrainer
from requests_futures.sessions import FuturesSession

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from app.core.fixing_links import url_constructor
from .base_provider import Provider


# TO DO: this file has a misleading name ("core")
logger = logging.getLogger(__name__)
core_base = 'https://mla.hcommons.org/wp-admin/admin-ajax.php'  # TO DO: this is a duplicate ... already in settings


def fetch_and_parse_items(follou, hit_limit, timeout):
    items = []
    count = 0

    with FuturesSession() as session:
        # Initiate requests
        futures = [session.get(f, timeout=timeout) for f in follou]

        for future in as_completed(futures[:hit_limit]):
            item = {}
            strainer = SoupStrainer(id="item-body")
            try:
                response = future.result()
                soup = BeautifulSoup(response.text, 'lxml', parse_only=strainer)

                # Extract title and meta information
                title_tag = soup.select_one('h3')
                meta_tags = soup.select('dd')

                if title_tag:
                    item['title'] = title_tag.get_text()

                if len(meta_tags) > 0:
                    item['author'] = meta_tags[0].get_text().replace('(see profile)', '').strip()

                if len(meta_tags) > 1:
                    try:
                        item['year'] = int(meta_tags[1].get_text())
                    except ValueError:
                        pass

                dl_tag = soup.select_one('dl')
                if dl_tag:
                    subjects = dl_tag.select('a[href*=subject_facet]')
                    item['subjects'] = [s.get_text() for s in subjects] if subjects else []

                    genre_tag = dl_tag.select_one('a[href*=genre_facet]')
                    item['type'] = genre_tag.get_text() if genre_tag else None

                    doi_tag = dl_tag.find('a', text=re.compile(r'doi'))
                    if doi_tag:
                        item['doi'] = doi_tag.get_text()
                        item['href'] = [
                            url_constructor(link.get_text(), link.get_text(), link.get('href'))
                            for link in [soup.select_one('a.bp-deposits-view'), doi_tag] if link
                        ]

                abstract_tag = soup.find('dt', text=re.compile(r'Abstract'))
                if abstract_tag:
                    item['abstract'] = abstract_tag.findNext('dd').get_text()

                item['rank'] = count
                item['query'] = 'https://hcommons.org/deposits/'
                count += 1
                items.append(item)
            except Exception as e:
                logger.debug(f"An error occurred: {e}")

    return items


def mlacore(
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

    title = title.replace('+', ' ')
    author = author.replace('+', ' ')

    s = requests.Session()

    if doi:
        search_terms = doi
    elif isbn:
        search_terms = isbn
    else:
        search_terms = author+title+year

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,es;q=0.7,fr;q=0.6",
        "content-length": "400",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://mla.hcommons.org",
        "referer": "https://mla.hcommons.org/deposits/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/68.0.3440.106 Chrome/68.0.3440.106 Safari/537.36"  # noqa:E501
    }

    data = {
        "action": "deposits_filter",
        "object": "deposit",
        "filter": "newest",
        "search_terms": search_terms,
        "scope": "all",
        "page": "1"
    }

    try:
        r = s.post(core_base, data=data, headers=headers, timeout=request_timeout)
        r.raise_for_status()
    except requests.exceptions.Timeout:
        logger.debug("The request timed out")
        result_queue.put({'core': hits})
        return {'core': hits}
    except requests.exceptions.RequestException as e:
        logger.debug(f"An error occurred: {e}")
        result_queue.put({'core': hits})
        return {'core': hits}

    response = r.text
    logger.debug(response)
    strain = SoupStrainer(id="deposits-stream")
    soup = BeautifulSoup(response, 'lxml', parse_only=strain)
    titles = soup.select('h4 > a')
    follou = ["https://mla.hcommons.org"+t.get('href') for t in titles]

    hits["hits"] = fetch_and_parse_items(follou, hit_limit, request_timeout)

    result_queue.put({'core': hits})
    return {'core': hits}

# TO DO: parse the payload ... filter and convert values  .. author missing atm and similar
class MLACOREProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from MLACORE ...")
        logger.debug(self.config)
        raw_items = self._fetch(request)

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]
        logger.debug(results)
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        query = self._build_query(request)
        logger.debug(query)
        try:
            r = requests.get(query)
            logger.debug(r.status_code)
        except Exception as e:
            logger.debug(e)
            return []

        results = r.json()
        logger.debug(results)
        if not results:
            return []

        # return results["hits"]["hits"]
        return [self._normalize_item(item) for item in results["hits"]["hits"]]

    def _build_query(self, request: SearchRequest) -> tuple:
        clauses = []

        if request.title:
            clauses.append(f'metadata.title:("{request.title}")')

        if request.author:
            clauses.append(f'metadata.author:("{request.author}")')

        if request.year:
            clauses.append(f'metadata.publication_date:({request.year})')

        query = "".join(clauses)
        params = {
            "q": query,
            "sort": "bestmatch",
            "page": 1,
            "size": request.hit_limit,
        }

        return f"{self.config.query_url}?{urlencode(params)}"

    def _fetch_content_url(self, item: dict) -> list:
        logger.debug(item)
        content_url = item["links"].get("files", "")
        logger.debug(content_url)
        if not content_url:
            return []
        try:
            r = requests.get(content_url)
            return [
                entry["links"].get("content")
                for entry in r.json()["entries"] 
                if "links" in entry
            ]
        except Exception as e:
            logger.debug(e)
        return []

    
    def _extract_authors(self, record: dict) -> list:
        output = []

        for creator in record.get("creators", []):
            person = creator.get("person_or_org", {})
            firstname = person.get("given_name", "")
            lastname = person.get("family_name", "")

            if not firstname and not lastname:
                full = person.get("name", "")
                if "," in full:
                    lastname, firstname = [x.strip() for x in full.split(",", 1)]

            author = {
                "name": f"{firstname} {lastname}".strip(),
                "alternate": [person.get("name", "")] if person.get("name") else [],
                "firstname": firstname,
                "lastname": lastname,
            }

            output.append(author)
        return output

    
    def _normalize_item(self, item: dict) -> dict:
        try:
            normalized = item["metadata"]
            normalized["links"] = item.get("links", "")
            normalized["landing_url"] = normalized["links"].get("self_html", "")
            normalized["doi"] = item["links"].get("doi", "")
            normalized["download_url"] = self._fetch_content_url(item["metadata"])
            normalized["creators"] = self._extract_authors(item["metadata"])
            logger.debug(normalized)
            return normalized
        except Exception as e:
            logger.debug(e)
            return {}
