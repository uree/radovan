import logging
import re
from typing import Iterable, List
from urllib.parse import quote_plus

import urllib.request
from bs4 import BeautifulSoup

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from app.core.fixing_links import url_constructor
from .base_provider import Provider


logger = logging.getLogger(__name__)
MONOSKOP_BASE = 'https://monoskop.org/log/?cat=17&s='
MONOSKOP_ROOT = 'https://monoskop.org/'


def monoskop(
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

    # unicode characters problematic for urrlib
    author = author.replace(' ', '+')
    author = author.replace('\xa0', '+')
    # apostrophe
    author = author.replace('\u2019', '')
    title = title.replace(' ', '+')
    title = title.replace('\u2019', '')
    # en dash _
    author = author.replace('\u2013', '')
    title = title.replace('\u2013', '')

    try:
        title = title.replace('”', '')
        title = title.replace('“', '')
    except Exception as e:
        logger.debug(e)
        pass

    if len(isbn) > 5:
        query = isbn
    else:
        query = author+'+'+title

    monoskop_url = MONOSKOP_BASE+query

    logger.debug(f"Making request {monoskop_url}")

    request = urllib.request.Request(
                monoskop_url,
                headers={"User-Agent": "Magic Browser"}
            )

    try:
        con = urllib.request.urlopen(request, timeout=request_timeout)
    except Exception as e:
        logger.debug(e)
        result_queue.put({'monoskop': hits})
        return {'monoskop': hits}

    logger.debug("Processing soup")
    soup = BeautifulSoup(con)
    items = soup.select(".item")
    logger.debug(soup)

    for i in items[:hit_limit]:
        mdata = {}

        title = i.select('h1')[0].get_text()
        landing = i.select('h1 a')[0].get('href')
        gt_imag = i.select('img')

        try:
            img_href = gt_imag[0].get('src')
        except IndexError:
            result_queue.put({'monoskop': hits})
            return {'monoskop': hits}

        if img_href.startswith('../'):
            img_href = 'https://monoskop.org/'+img_href[3:]
        else:
            pass

        isbn = re.search('(ISBN)(.*)', str(i))
        isbns = []

        if isbn:
            for z in isbn.group(2).split(','):
                z = z.strip()
                z = re.sub('[^0-9]','', z)
                isbns.append(z)
        else:
            pass

        links = i.find_all('a')

        up = gt_imag[0].parent
        side = up.next_siblings

        links = []
        not_links = []

        # this relies on the cover image being found = not great
        for x in side:
            try:
                m = x.find_all('a')
                if len(m) == 0:
                    not_links.append(x.text)
                else:
                    for y in m:
                        qck_dct = {}

                        if y.text.startswith('Comment'):
                            pass
                        else:
                            out = y.get('href')
                            if out.startswith('../'):
                                out = 'https://monoskop.org/'+out[3:]
                            else:
                                pass

                            qck_dct['type'] = y.text
                            qck_dct['name'] = y.text
                            qck_dct['href'] = str(out)
                            links.append(qck_dct)
            except:
                pass

        desc = '\n'.join(not_links)
        mdata['img_href'] = img_href
        mdata['desc'] = desc

        # problematic fields
        links.append(url_constructor('landing', 'landing_url', landing))
        mdata['href'] = links
        mdata['title'] = title

        mdata['query'] = monoskop_url

        mdata['isbn'] = isbns
        mdata['type'] = 'book'

        hits['hits'].append(mdata)

    result_queue.put({'monoskop': hits})
    return {'monoskop': hits}


class MonoskopProvider(Provider):
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        logger.debug("Fetching from Monoskop ...")
        raw_items = self._fetch(request)

        results = [
            self.to_bibrecord(item).to_dict()
            for item in raw_items
        ]

        logger.debug(results)
        return results

    def _fetch(self, request: SearchRequest) -> List[dict]:
        monoskop_url = MONOSKOP_BASE + self._build_query(request)
        logger.debug(f"Making request {monoskop_url}")

        provider_request = urllib.request.Request(
            monoskop_url,
            headers={"User-Agent": "Magic Browser"}
        )

        try:
            response = urllib.request.urlopen(
                provider_request,
                timeout=request.request_timeout
            )
        except Exception as e:
            logger.debug(e)
            return []

        soup = BeautifulSoup(response, 'lxml')
        items = soup.select(".item")

        results = []
        for item in items[:request.hit_limit]:
            normalized = self._normalize_item(item, monoskop_url)
            if normalized:
                results.append(normalized)

        return results

    def _build_query(self, request: SearchRequest) -> str:
        if request.isbn:
            return quote_plus(request.isbn)

        search_terms = " ".join(
            part
            for part in [
                request.author,
                request.title,
                request.year,
            ]
            if part
        )

        return quote_plus(search_terms)

    def _normalize_item(self, item, query: str) -> dict | None:
        try:
            title = item.select('h1')[0].get_text()
            landing = item.select('h1 a')[0].get('href')
            image = item.select('img')[0]
        except IndexError as e:
            logger.debug(e)
            return None

        img_href = self._absolute_url(image.get('src', ''))
        links, description_parts = self._extract_links_and_description(image)

        if landing:
            links.append(
                url_constructor(
                    'landing',
                    'landing_url',
                    self._absolute_url(landing)
                )
            )

        return {
            'img_href': img_href,
            'desc': '\n'.join(description_parts),
            'href': links,
            'title': title,
            'query': query,
            'isbn': self._extract_isbns(item),
            'type': 'book',
        }

    def _extract_links_and_description(self, image) -> tuple[list[dict], list[str]]:
        links = []
        description_parts = []

        # This relies on the cover image position in Monoskop's item markup.
        for sibling in image.parent.next_siblings:
            try:
                anchors = sibling.find_all('a')
            except AttributeError:
                continue

            if not anchors:
                text = sibling.get_text(strip=True)
                if text:
                    description_parts.append(text)
                continue

            for anchor in anchors:
                if anchor.text.startswith('Comment'):
                    continue

                href = anchor.get('href')
                if not href:
                    continue

                links.append({
                    'type': anchor.text,
                    'name': anchor.text,
                    'href': self._absolute_url(href),
                })

        return links, description_parts

    # TO DO: is this func reusable elsewhere?
    def _extract_isbns(self, item) -> list[str]:
        isbn = re.search('(ISBN)(.*)', str(item))
        if not isbn:
            return []

        isbns = []
        for value in isbn.group(2).split(','):
            value = value.strip()
            value = re.sub('[^0-9]', '', value)
            if value:
                isbns.append(value)

        return isbns

    def _absolute_url(self, url: str) -> str:
        if url.startswith('../'):
            return MONOSKOP_ROOT + url[3:]

        if url.startswith('/'):
            return MONOSKOP_ROOT.rstrip('/') + url

        return url
