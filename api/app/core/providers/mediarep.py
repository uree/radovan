import logging
import requests
from concurrent.futures import as_completed

from bs4 import BeautifulSoup, SoupStrainer
from requests_futures.sessions import FuturesSession

from fixing_links import url_constructor


logger = logging.getLogger(__name__)
mediarep_base = 'https://mediarep.org/discover?'


def mediarep(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    logger.info("Searching mediarep ...")
    hits = {'hits': []}
    count = 0

    query = mediarep_base+ 'filtertype_1=title&filter_relational_operator_1=contains&filter_1='+title+'&filtertype_2=author&filter_relational_operator_2=contains&filter_2='+author+'&query=&scope='
    r = requests.get(query)
    response = r.text
    strain = SoupStrainer(id="aspect_discovery_SimpleSearch_div_search-results")
    soup = BeautifulSoup(response, 'lxml', parse_only=strain)

    titles = soup.select('a')
    follou = ["https://mediarep.org"+t.get('href')+'?show=full' for t in titles]
    #localhost:9003/v1.0/simple/items?author=&title=hacking&year=&isbn=&doi=&sources=12

    with FuturesSession() as session:
        results = [session.get(f) for f in follou]

        for r in as_completed(results[:hit_limit]):
            item = {}
            # i can get it ALL from the meta tags
            strainer = SoupStrainer("meta")
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
            count+=1
            hits['hits'].append(item)

    logger.debug(hits)
    result_queue.put({'mediarep': hits})
    return {'mediarep': hits}
