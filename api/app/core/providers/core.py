import logging
import re
import requests
from concurrent.futures import as_completed

from bs4 import BeautifulSoup, SoupStrainer
from requests_futures.sessions import FuturesSession

from fixing_links import url_constructor


logger = logging.getLogger(__name__)
core_base = 'https://mla.hcommons.org/wp-admin/admin-ajax.php'


def core(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    # print("Searching core ...")
    logger.info("Searching core ...")
    hits = {'hits': []}
    count = 0


    title = title.replace('+', ' ')
    author = author.replace('+', ' ')

    doi_add = 'http://dx.doi.org/'

    s = requests.Session()

    if doi:
        search_terms = doi
    elif isbn:
        search_terms = isbn
    else:
        search_terms = author+title+year

    headers = {"accept": "*/*", "accept-encoding": "gzip, deflate, br", "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,es;q=0.7,fr;q=0.6", "content-length": "400", "content-type": "application/x-www-form-urlencoded; charset=UTF-8", "origin": "https://mla.hcommons.org", "referer": "https://mla.hcommons.org/deposits/", "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/68.0.3440.106 Chrome/68.0.3440.106 Safari/537.36"}

    data = {"action": "deposits_filter", "object": "deposit", "filter": "newest", "search_terms": search_terms, "scope": "all", "page": "1"}


    r = s.post(core_base, data=data, headers=headers)
    response = r.text

    strain = SoupStrainer(id="deposits-stream")
    soup = BeautifulSoup(response, 'lxml', parse_only=strain)


    titles = soup.select('h4 > a')

    follou = ["https://mla.hcommons.org"+t.get('href') for t in titles]


    # request-futures
    with FuturesSession() as session:
        results = [session.get(f) for f in follou]

        for r in as_completed(results[:hit_limit]):
            item = {}
            strainer = SoupStrainer(id="item-body")
            suppchen = BeautifulSoup(r.result().text, 'lxml', parse_only=strainer)

            title = suppchen.select_one('h3').get_text()
            meta = suppchen.select('dd')

            item['title'] = title
            item['author'] = meta[0].get_text().replace('(see profile)','').strip()

            try:
                item['year'] = int(meta[1].get_text())
            except Exception as e:
                pass

            dl = suppchen.select_one('dl')

            subjects = dl.select('a[href*=subject_facet]')
            try:
                item['subjects'] = [s.get_text() for s in subjects]
            except Exception as e:
                #logger.debug('Extraction error in core(): ', e)
                pass
            try:
                item['type'] = dl.select_one('a[href*=genre_facet]').get_text()
            except Exception as e:
                #logger.debug('Extraction error in core(): ', e)
                pass

            link = suppchen.select_one('a.bp-deposits-view')
            doi = dl.find('a', text=re.compile(r'doi'))

            try:
                item['href'] = []
                i = url_constructor(link.get_text(), link.get_text(), link.get('href'))
                j = url_constructor('landing', 'landing_url', 'https://hcommons.org'+doi.get('href'))
                item['href'].append(i)
                item['href'].append(j)
            except Exception as e:
                del item['href']
                #logger.debug('Error constructing urls in core(): ', e)
                pass

            try:
                item['doi'] = doi.get_text()
            except Exception as e:
                pass
            try:
                item['abstract'] = suppchen.find('dt', text=re.compile(r'Abstract')).findNext('dd').get_text()
            except Exception as e:
                pass


            item['rank'] = count
            item['query'] = 'https://hcommons.org/deposits/'
            count+=1
            hits['hits'].append(item)

    result_queue.put({'core': hits})
    return {'core': hits}
