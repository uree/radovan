import logging
import requests
from typing import Iterable, List
from urllib.parse import urlencode

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
from app.core.fixing_links import url_constructor
from .utils import fetch_provider

logger = logging.getLogger(__name__)
osf_base = 'https://share.osf.io/api/v2/search/creativeworks/_search'


def osf(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=10,
    request_timeout=5
):
    count = 0

    hits = {'hits': []}

    if doi:
        query = '?q='+doi+'&type=preprint'
    else:
        if len(author) > 1:
            part2 = 'contributors:'+author
        else:
            part2 = ''

        if len(title) > 1:
            part3 = 'title:'+title
        else:
            part3 = ''

        if len(year) > 1:
            part4 = 'year:'+year
        else:
            part4 = ''

        query = '?size='+str(hit_limit)+'&q='+part2+part3+part4

    osf_url = osf_base+query
    headers = {'Content-Type': 'application/json'}

    results = fetch_provider(
        "osf",
        osf_url,
        headers,
        request_timeout=request_timeout,
        format="json"
    )
    logger.debug(results)

    if not results:
        result_queue.put({'osf': hits})
        return {'osf': hits}

    for i in results['hits']['hits']:
        i['_source']['rank'] = count
        i['_source']['landing_url'] = 'https://share.osf.io/preprint/'+i['_id']
        i['_source']['query'] = osf_url
        try:
            ls = []
            ls.append(url_constructor('landing', 'landing_url', i['_source']['identifiers'][0]))
            i['_source']['links'] = ls
        except Exception as e:
            logger.debug('Issue with parsing data in osf(): ', e)
            pass

        count += 1
        hits['hits'].append(i['_source'])

    result_queue.put({'osf': hits})
    return {'osf': hits}


class OSFProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from OSF ...")
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

        results = fetch_provider(
            "osf",
            query,
            {"Content-Type": "application/json"},
            request_timeout=request.request_timeout,
            format="json"
        )
        logger.debug(results)

        if not results:
            return []
        # normalize if need be
        try:
            return [
                self._normalize_item(item)
                for item in results["hits"]["hits"][:request.hit_limit]
            ]
        except Exception as e:
            logger.debug(e)
            return []

    def _build_query(self, request: SearchRequest) -> str:
        search_query = " ".join(
            part
            for part in (
                f"contributors:{request.author}" if request.author else None,
                f"title:{request.title}" if request.title else None,
                f"year:{request.year}" if request.year else None,
            )
            if part
        )

        params = {
            "q": search_query,
            "size": request.hit_limit,
        }
        return f"{self.config.query_url}?{urlencode(params)}"
    # TO DO: works for now, revisit when refactoring bibjson_methods
    def _normalize_item(self, item: dict) -> dict:
        normalized = item["_source"].copy()

        identifiers = normalized.get("identifiers")
        if identifiers:
            identifier = identifiers[0]
            normalized["landing_url"] = identifier
            normalized["doi"] = identifier
        else:
            logger.debug("No identifiers found")

        date = normalized.get("date")
        if isinstance(date, str) and len(date) >= 4:
            normalized["year"] = date[:4]
        else:
            logger.debug("Could not derive year from date: %r", date)

        return normalized