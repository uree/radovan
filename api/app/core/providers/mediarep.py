import logging
import requests
from concurrent.futures import as_completed

from bs4 import BeautifulSoup, SoupStrainer
from requests_futures.sessions import FuturesSession

from fixing_links import url_constructor
from .utils import fetch_provider


logger = logging.getLogger(__name__)
mediarep_base = 'https://mediarep.org/search?spc.page=1&f.itemtype=book,equals'



def fetch_and_parse_items(follou, hit_limit, request_timeout, query):
    items = []
    count = 0

    with FuturesSession() as session:
        results = [session.get(f, timeout=request_timeout) for f in follou]

        for r in as_completed(results[:hit_limit]):
            item = {}
            # i can get it ALL from the meta tags
            strainer = SoupStrainer("meta")
            try:
                suppchen = BeautifulSoup(r.result().text, 'lxml', parse_only=strainer)
                #print(suppchen)
                try:
                    item['title'] = suppchen.select_one('meta[name="DC.title"]')['content']
                except TypeError:
                    pass

                try:
                    item['year'] = suppchen.select_one('meta[name="DCTERMS.issued"]')['content']
                except TypeError:
                    pass

                try:
                    item['doi'] = suppchen.select_one('meta[name="citation_doi"]')['content']
                except TypeError:
                    pass

                try:
                    href = suppchen.select_one('meta[name="citation_pdf_url"]')['content']
                    item['href'] = url_constructor('open', 'open_url', href)
                except TypeError:
                    pass

                try:
                    item['isbn'] = suppchen.select_one('meta[content^="isbn:"]')['content'].replace('isbn:', '')
                except TypeError:
                    pass

                # plethora of authorita
                creators = suppchen.select('meta[name="DC.creator"]')
                editors = suppchen.select('meta[name="DC.editor"]')

                # strained
                if editors:
                    try:
                        item['editor'] = [e['content'] for e in editors]
                    except:
                        pass
                if creators:
                    try:
                        item['author'] = [c['content'] for c in creators]
                    except:
                        pass

                item['rank'] = count
                item['query'] = query
                count += 1
                items.append(item)
            except Exception as e:
                logger.debug(f"An error occurred: {e}")

    return items


def mediarep(
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

    query = mediarep_base + f"&query={title}&f.itemtype=book,equals"
    if author:
        query += f"&f.author={author},equals"

    results = fetch_provider(
        "mediarep",
        query,
        None,
        request_timeout=request_timeout,
        format="text"
    )
    logger.debug(results)

    if not results:
        result_queue.put({'mediarep': hits})
        return {'mediarep': hits}

    strain = SoupStrainer(id="aspect_discovery_SimpleSearch_div_search-results")
    soup = BeautifulSoup(results, 'lxml', parse_only=strain)

    titles = soup.select('a')
    follou = ["https://mediarep.org"+t.get('href')+'?show=full' for t in titles]

    hits['hits'] = fetch_and_parse_items(follou, hit_limit, request_timeout, query)

    logger.debug(hits)
    result_queue.put({'mediarep': hits})
    return {'mediarep': hits}
