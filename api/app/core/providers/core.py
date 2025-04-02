import logging
import re
import requests
from concurrent.futures import as_completed

from bs4 import BeautifulSoup, SoupStrainer
from requests_futures.sessions import FuturesSession

from fixing_links import url_constructor


logger = logging.getLogger(__name__)
core_base = 'https://mla.hcommons.org/wp-admin/admin-ajax.php'


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


def core(
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
