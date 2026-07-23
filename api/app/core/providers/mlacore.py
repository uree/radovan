import logging
import requests
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from .base_provider import Provider


logger = logging.getLogger(__name__)


class MLACOREProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from MLACORE ...")
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
