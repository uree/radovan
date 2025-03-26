import logging
import re
import requests

from bs4 import BeautifulSoup

from fixing_links import url_constructor


logger = logging.getLogger(__name__)
libgen_home = 'https://libgen.is'
libgen_base_articles = libgen_home+"/scimag/?"


def libgen_article(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching libgen_article ...")
    logger.debug("Searching libgen_article ...")

    hits = {'hits': []}
    count = 0

    if doi:
        query = 'q='+doi
    else:
        query = 'q='+title+'+'+author

    libgen_url = libgen_base_articles+query

    r = requests.get(libgen_url)
    soup = BeautifulSoup(r.text, 'lxml')
    rows = soup.select(".catalog > tbody > tr")

    for i in rows[:hit_limit]:
        item = {}
        journal = {'name': '', 'volume': '', 'issue': '', 'year':''}

        tds = i.select('td')
        try:
            auth_data = tds[0].get_text().split(';')
        except:
            auth_data = tds[0].get_text()

        # check for impurities
        item['landing_url'] = libgen_home+'/'+tds[1].a.get('href')

        get_doi = tds[1].a.get('href').split("scimag/")[-1]
        get_title = tds[1].a.get_text()

        try:
            journal_data = tds[2].select('p')
            journal['name'] = journal_data[0].get_text()
            journal_info = re.findall(r'\d+', journal_data[1].get_text())
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)

        try:
            journal['volume'] = journal_info[0]
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)
        try:
            journal['issue'] = journal_info[1]
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)

        try:
            journal['year'] = journal_info[2]
        except Exception as e:
            logger.debug("Error extractig journal info @libgen_article: ", e)

        links = tds[4].select('a')

        item['href'] = [url_constructor(l.get_text(), l.get_text(), l.get('href')) for l in links]
        item['rank'] = count
        item['query'] = libgen_url


        item['author'] = auth_data
        item['doi'] = get_doi
        item['title'] = get_title
        item['journal'] = journal
        hits['hits'].append(item)
        count+=1

    result_queue.put({'libgen_article': hits})
    return {'libgen_article': hits}
