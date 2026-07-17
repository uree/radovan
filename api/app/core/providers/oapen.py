import logging
from typing import Iterable, List
from urllib.parse import quote_plus

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider
from .utils import fetch_provider

logger = logging.getLogger(__name__)
OAPEN_BASE = 'https://library.oapen.org/rest/search?query='
OAPEN_HANDLE_BASE = 'https://library.oapen.org/handle'
OAPEN_BITSTREAM_BASE = 'https://library.oapen.org/bitstream/handle'


def oapen(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=3,
    request_timeout=5
):

    if len(isbn) > 2:
        query = isbn+'&expand=metadata,bitstreams'+'&limit='+str(hit_limit)
    elif len(doi) > 2:
        query = doi+'&expand=metadata,bitstreams'+'&limit='+str(hit_limit)
    else:
        query = author+title+year+'&expand=metadata,bitstreams'+'&limit='+str(hit_limit)

    oapen_url = OAPEN_BASE+query

    hits = {'hits': []}

    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0"}  # noqa:501

    results = fetch_provider(
        "oapen",
        oapen_url,
        headers,
        request_timeout=request_timeout,
        format="json"
    )

    if not results:
        result_queue.put({'oapen': hits})
        return {'oapen': hits}

    for i in range(len(results)):
        # there are multiple bitstreams (images, multiple text formats); only using one for now
        try:
            bit = results[i]['bitstreams'][0]
        except:
            bit = None
        try:
            bit_meta = results[i]['bitstreams'][0]['metatada']
        except:
            bit_meta = None

        if bit_meta:
            for b in bit_meta:
                # extract download url
                if b['key'] == 'dc.identifier.uri':
                    results[i]['url'] = b['value']

        if bit:
            results[i]['standard_oapen_url'] = OAPEN_BITSTREAM_BASE+'/'+results[i]['handle']+'/'+bit['name']  # noqa:501

            results[i]['coverurl'] = OAPEN_BITSTREAM_BASE+'/'+results[i]['handle']+'/'+bit['name']+'.jpg'  # noqa:501

        for m in results[i]['metadata']:
            results[i][m['key']] = m['value']

        del results[i]['metadata']
        del results[i]['bitstreams']
        # confuses bibjson_methods and is a duplicate of dc.title anyway
        del results[i]['name']
        # by default these are /rest links and they take you to an xml page
        results[i]['link'] = OAPEN_HANDLE_BASE+'/'+results[i]['handle']

    hits['hits'] = results[:3]
    logger.debug(hits)

    result_queue.put({'oapen': hits})
    return {'oapen': hits}


class OAPENProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from OAPEN ...")
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
        oapen_url = OAPEN_BASE + query

        headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0"}  # noqa:501

        results = fetch_provider(
            "oapen",
            oapen_url,
            headers,
            request_timeout=request.request_timeout,
            format="json"
        )
        logger.debug(results)

        if not results:
            return []

        return [
            self._normalize_item(item)
            for item in results[:request.hit_limit]
        ]

    def _build_query(self, request: SearchRequest) -> str:
        if request.isbn:
            search_terms = request.isbn
        elif request.doi:
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

        return (
            f"{quote_plus(search_terms)}"
            f"&expand={quote_plus('metadata,bitstreams')}"
            f"&limit={request.hit_limit}"
        )

    def _normalize_item(self, item: dict) -> dict:
        normalized = {
            key: value
            for key, value in item.items()
            if key not in {"metadata", "bitstreams", "name"}
        }

        handle = item.get("handle")
        if handle:
            normalized["link"] = f"{OAPEN_HANDLE_BASE}/{handle}"

        for metadata in item.get("metadata", []):
            key = metadata.get("key")
            value = metadata.get("value")
            if key and value:
                normalized[key] = value

        for bitstream in item.get("bitstreams", []):
            bitstream_name = bitstream.get("name")

            if handle and bitstream_name:
                bitstream_url = f"{OAPEN_BITSTREAM_BASE}/{handle}/{bitstream_name}"
                normalized["standard_oapen_url"] = bitstream_url
                normalized["coverurl"] = f"{bitstream_url}.jpg"

            for metadata in bitstream.get("metadata", []):
                if metadata.get("key") != "dc.identifier.uri":
                    continue

                download_url = metadata.get("value")
                if download_url:
                    normalized["url"] = download_url

            return normalized

        return normalized
