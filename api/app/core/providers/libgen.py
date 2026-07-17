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
LIBGEN_HOME = "https://libgen.vg"
LIBGEN_BASE = LIBGEN_HOME + "/index.php"
LIBGEN_API = LIBGEN_HOME + "/json.php"
LIBGEN_DL_ADDRESS = "https://download.books.ms/main/"  # deprecated
LIBGEN_COVER_ADDRESS = LIBGEN_HOME + "/covers"


def update_libgen_json(data):
    tmp = []

    for d in data:
        cover_url = LIBGEN_COVER_ADDRESS
        +d['coverurl']
        magic_number = d['coverurl'].split('/')[0]

        # generate download url
        download_url = LIBGEN_DL_ADDRESS+magic_number+'/'+d['md5']+'/'+d['locator']

        # update
        # TO DO: so is it landing or download?
        d['coverurl'] = cover_url
        mini_locator = {'type': 'landing_url', 'href': download_url, 'name': 'landing'}
        d['locator'] = mini_locator
        d['landing_url'] = LIBGEN_HOME+'/book/index.php?md5='+d['md5']
        tmp.append(d)

    return tmp

def update_libgen_src(lst, target):
    srcs = [LIBGEN_HOME+l.get(target).replace('..', '') for l in lst]  # noqa
    return srcs


def handle_isbn_query_results(results, libgen_books_url):
    try:
        good_links = update_libgen_json(results)
    except Exception as e:
        logger.debug(e)
        good_links = None

    if good_links is not None:
        for n in range(len(good_links)):
            good_links[n]['rank'] = n
            good_links[n]['query'] = libgen_books_url

        return good_links

    return []


def handle_normal_query_results(results, hit_limit, query):
    logger.debug("handle query called")
    count = 0
    hits = []

    # parse links
    soup = BeautifulSoup(results, 'lxml')
    logger.debug(soup)
    get_hrefs_init = soup.select('a[href*="edition.php?id"]')
    logger.debug(get_hrefs_init)
    href_urls = update_libgen_src(get_hrefs_init, 'href')
    logger.debug(href_urls)

    # set limit here ... lowest query = 25
    get_hrefs = href_urls[:hit_limit]


    # prepare links for processing
    new_hrefs = [LIBGEN_API+"?object=e&ids"+g.split('id')[-1]+"&fields=*" for g in get_hrefs]
    logger.debug(new_hrefs)

    # fetch metadata
    for hr in new_hrefs:
        record = requests.get(hr).json()
        logger.debug(record)

        # extends urls with domain names and classifies them
        # be careful data needs to be a list (or update_libgen_json needs to be upgraded)
        try:
            good_links = update_libgen_json(record)
        except Exception as e:
            logger.debug(e)
            good_links = [{'error': 'libgen record parsing error'}]

        # add to the record
        # good_links[0]['rank'] = count
        # good_links[0]['query'] = query
        # count += 1
        hits.append(good_links[0])

    return hits


def libgen_book(
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

    # isbn or doi query can go straight to fetching & parsing json

    if len(isbn) > 8:
        try:
            hem = isbn.split(' ')
            isbn = hem[0]
        except Exception as e:  # noqa
            pass
        query = "isbn="+isbn+"&fields=*"
        libgen_books_url = LIBGEN_BASE+query
        headers = {"Connection": "close"}
        format = "json"
    # other queries fetch links for fetching json first
    else:
        query = author+'+'+title+'+'+year
        libgen_books_url = LIBGEN_HOME+"/search.php?req="+query+"&open=0&res=25&view=detailed&phrase=1&column=def"  # noqa:501
        headers = None
        format = "text"

    results = fetch_provider(
        "libgen_book",
        libgen_books_url,
        headers,
        request_timeout=request_timeout,
        format=format
    )

    if not results:
        result_queue.put({'libgen_book': hits})
        return {'libgen_book': hits}

    if len(isbn) > 8:
        hits['hits'] = handle_isbn_query_results(results, libgen_books_url)
    else:
        hits['hits'] = handle_normal_query_results(results, hit_limit, libgen_books_url)

    result_queue.put({'libgen_book': hits})
    return {'libgen_book': hits}


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
                "libgen_book",
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
                "libgen_book",
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
            return f"{LIBGEN_API}json.php?object=e&doi={request.doi}"
        elif request.isbn:
            return f"{LIBGEN_API}json.php?object=e&isbn={request.isbn}"
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
            return f"{LIBGEN_BASE}?req={quote_plus(search_terms)}&res={request.hit_limit}"

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
            item["cover_url"] = f"{LIBGEN_COVER_ADDRESS}/{libgen_id[:4] + "000"}.jpg" if libgen_id else ""
        # TO DO: download url does not end up in api response and is not really a download link (= landing url libgen download)
        item["download_url"] = f"{LIBGEN_HOME}/ads.php?md5={md5}" if md5 else ""
        item["landing_url"] = f"{LIBGEN_HOME}/file.php?md5={md5}" if md5 else ""

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
            f"{LIBGEN_API}?object=e&ids={id_}&fields=*&addkeys=*"
            for id_ in ids
        ]

        return api_urls
