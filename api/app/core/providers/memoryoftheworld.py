import logging
import requests
from typing import Iterable, List

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord

from .base_provider import Provider

logger = logging.getLogger(__name__)
memory_base = 'https://library.memoryoftheworld.org/'


def memoryoftheworld(
    result_queue,
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    hit_limit=10,
    request_timeout=5
):

    url_authors = "https://library.memoryoftheworld.org/search/authors/"
    url_title = "https://library.memoryoftheworld.org/search/title/"
    url_isbn = "https://library.memoryoftheworld.org/search/_isbn/"

    hits = {'hits': []}
    count = 0

    # it is actually less acurate if you remove ':'
    if len(isbn) > 2:
        isbn_prep = isbn.strip().replace('-', '')
        query = url_isbn+isbn_prep
    elif len(author) >= 2 and len(title) <= 2:
        auth_prep = author.replace(' ', '+')
        query = url_authors+auth_prep
    elif len(title) >= 2 and len(author) <= 2:
        title_prep = title.replace(' ', '+')
        query = url_title+title_prep
    elif len(title) >= 2 and len(author) >= 2:
        title_prep = title.replace(' ', '+')
        query = url_title+title_prep
    else:
        result_queue.put({'memoryoftheworld': hits})
        return {'memoryoftheworld': hits}

    logger.debug(query)

    try:
        r = requests.get(query, verify=False, timeout=request_timeout) # ssl
        data = r.json()
    except requests.exceptions.SSLError:
        data = {"_items": []}

    if len(data['_items']) > 0:

        for i in data['_items'][:hit_limit]:
            output = {}
            url_base = 'https:'+i['library_url']
            linksos = []

            for f in i['formats']:
                try:
                    href = url_base+f['dir_path']+f['file_name']
                    text = f['format']
                    link = dict({'href': href, 'format': text.lower()})
                    linksos.append(link)
                except:
                    pass

            output['author'] = [n for n in i['authors']]
            output['title'] = i['title']
            output['rank'] = count
            output['href'] = linksos
            output['type'] = 'book'
            output['query'] = query
            output['img_href'] = url_base+i['cover_url']
            hits['hits'].append(output)
            count += 1

    logger.debug(hits)

    result_queue.put({'memoryoftheworld': hits})
    return {'memoryoftheworld': hits}


class MOTWProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from memoryoftheworld ...")
        # does not support doi or year
        if request.doi or request.year:
            return []
        
        raw_items = self._fetch(request)
        # consider this: return results meta like count

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]
        logger.debug("we never got here have we")
        logger.debug(results)

        logger.debug(results)
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        query = self._build_query(request)

        try:
            r = requests.get(query, verify=False, timeout=request.request_timeout) # ssl
            results = r.json()["_items"]
        except requests.exceptions.SSLError:
            return []
        except Exception as e:
            logger.debug(e)
            return []
        # logger.debug(results)

        return [
            self._normalize_item(item)
            for item in results[:request.hit_limit]
        ]

    def _build_query(self, request: SearchRequest) -> str:
        url_authors = "https://library.memoryoftheworld.org/search/authors/"
        url_title = "https://library.memoryoftheworld.org/search/title/"
        url_isbn = "https://library.memoryoftheworld.org/search/_isbn/"

        if request.isbn:
            return f"{url_isbn}{request.isbn}"
        
        if request.author and request.title:
            return f"{url_title}{request.title}"

        if request.author:
            return f"{url_authors}{request.author}"

        if request.title:
            return f"{url_title}{request.title}"

    def _normalize_item(self, item: dict) -> dict:
        output = {}

        url_base = f"{self.config.url}{item['library_url']}"
        linksos = []

        for f in item["formats"]:
            try:
                href = f"{url_base}{f['dir_path']}{f['file_name']}"
                text = f["format"]

                linksos.append({
                    "href": href,
                    "format": text.lower()
                })

            except Exception as e:
                logger.debug(e)
                continue

        output["author"] = [n for n in item["authors"]]
        output["title"] = item["title"]
        output["href"] = linksos
        output["type"] = "book"
        output["img_href"] = f"{url_base}{item['cover_url']}"

        return output

