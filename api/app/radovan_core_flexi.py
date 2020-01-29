# -*- coding: utf-8 -*-
# python 3.6.9

import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import requests
import json
from bs4 import BeautifulSoup, SoupStrainer
import lxml.html
import lxml.etree
from lxml import etree
import re
import sys
import time

import dryscrape
from robobrowser import RoboBrowser
from requests import Session
import xmltodict
from io import StringIO, BytesIO
import pprint
import bibtexparser
import ast

import cProfile, pstats, io
from fixing_links import update_libgen_src, update_libgen_json, url_constructor

from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
from multiprocessing import Process, Queue

import logging

# GENERAL SETTINGS
logging.basicConfig(filename='logs/radovan_core_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
pp = pprint.PrettyPrinter(indent=4)

global_hit_limit = 10

#base urls
doaj_base = 'http://doaj.org/api/v1/search/articles/'
doab_base = 'http://www.doabooks.org/doab?func=search&query='
osf_base = 'https://share.osf.io/api/v2/search/creativeworks/_search'
memory_base = 'https://library.memoryoftheworld.org/'
oapen_base = 'http://www.oapen.org/search?'
openedition_base = 'http://books.openedition.org/'
core_base = 'https://mla.hcommons.org/wp-admin/admin-ajax.php'
scielo_base = 'http://search.scielo.org/?q='
opendoar_base = 'http://opendoar.org/api.php'
monoskop_base = 'https://monoskop.org/log/?cat=17&s='
oadoi_base = 'https://api.unpaywall.org/v2/'

libgen_home = "http://libgen.unblocked.name"
libgen_base_articles = libgen_home+"/scimag/?"
libgen_base_books = libgen_home+"/json.php?"

aaaaarg_search_base = 'http://aaaaarg.fail/search?query='
aaaaarg_makers_base = 'http://aaaaarg.fail/search/makers?query='
aaaaarg_things_base = 'https://aaaaarg.fail/search/things?query='
aaaaarg_base = 'http://aaaaarg.fail'
aaaaarg_username = ""
aaaaarg_password = ""


sources_dict = [{'full_name': 'Directory of Open Access Books', 'url': 'https://www.doabooks.org/', 'code_name': 'doab' ,'id': 0, 'books': 1, 'articles': 0, 'query_url': 'http://www.doabooks.org/doab?func=search&query='}, {'full_name': 'OAPEN', 'url': 'http://www.oapen.org/home', 'code_name': 'oapen' ,'id': 1, 'books': 1, 'articles': 0, 'query_url': 'http://www.doabooks.org/doab?func=search&query='}, {'full_name': 'Monoskop', 'url': 'https://monoskop.org/Monoskop', 'code_name': 'monoskop' ,'id': 2, 'books': 1, 'articles': 1, 'query_url': 'https://monoskop.org/log/?cat=17&s='},     {'full_name': 'Library Genesis', 'url': 'http://gen.lib.rus.ec/', 'code_name': 'libgen_book' ,'id': 3, 'books': 1, 'articles': 0, 'query_url': 'http://libgen.unblocked.name/json.php?'}, {'full_name': 'Library Genesis Scimag', 'url': 'http://gen.lib.rus.ec/scimag/index.php', 'code_name': 'libgen_article' ,'id': 4, 'books': 0, 'articles': 1, 'query_url': 'http://libgen.unblocked.name/scimag/index.php?'}, {'full_name': 'AAAAARG', 'url': 'http://aaaaarg.fail', 'code_name': 'aaaaarg', 'id': 5, 'books': 0, 'articles': 0, 'query_url': 'http://aaaaarg.fail/search?query='}, {'full_name': 'MLA Commons CORE', 'url': 'https://mla.hcommons.org/deposits/', 'code_name': 'core', 'id': 6, 'books': 1, 'articles': 1, 'query_url': 'https://mla.hcommons.org/wp-admin/admin-ajax.php'}, {'full_name': 'SciELO', 'url': 'http://www.scielo.org/', 'code_name': 'scielo' ,'id': 7, 'books': 0, 'articles': 1, 'query_url': 'http://search.scielo.org/?q='}, {'full_name': 'Memory of The World', 'url': 'http://library.memoryoftheworld.org/', 'code_name': 'memoryoftheworld' ,'id': 8, 'books': 0, 'articles': 0, 'query_url': 'https://library.memoryoftheworld.org/'}, {'full_name': 'Directory of Open Access Journals', 'url': 'https://doaj.org/', 'code_name': 'doaj', 'id': 9, 'books': 0, 'articles': 1, 'query_url': 'http://doaj.org/api/v1/search/articles/'}, {'full_name': 'Open Science Framework', 'url': 'https://osf.io/search/', 'code_name': 'osf' , 'id': 10, 'books': 0, 'articles': 1, 'query_url': 'https://share.osf.io/api/v2/search/creativeworks/_search'},   {'full_name': 'Unpaywall', 'url': 'https://unpaywall.org/data', 'code_name': 'oadoi' , 'id': 11, 'books': 0, 'articles': 1, 'query_url': 'https://api.unpaywall.org/v2/'}]

sources_short = {}

for i in sources_dict:
    sources_short[i['id']] = i['code_name']

# BULK SEARCH SETTINGS
bibjson_location = "tests/ch1_nolinks.json"
output_filename = bibjson_location[:-5]+'_links.json'
output_filename = "tests/testing.json"



# PROFILING, TIMING
def profile(fnc):

    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        # ... do something ...
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return inner


# GENERAL PURPOSE FUNCTIONS
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# if entry already has url
def url_rewrite(source, entry):
    if 'url' in entry:
        try:
            entry['url'] = url_constructor(source, entry['url'])
            return entry['url']
        except IndexError:
            print("no original links for "+entry['title'])
            #return None
            pass
    else:
        try:
            entry['url'] = ''
        except IndexError:
            pass

# ris to dict
def rtd(string):
    logging.info("Converting RIS to dictionary ... (1)")
    indict = {}
    for i in string:

        # some oapen ris records contain a weird double SN
        if re.match(r"SN.+SN", i.decode()) != None:
            spt = i.decode().split('-')[2]
            one = "ISBN"
            two = spt[-1].strip()
        else:
            try:
                spt = i.decode().split('-')
            except Exception as e:
                logging.debug("Error at split: ", e)
                pass

            try:
                one = spt[0].strip()
            except Exception as e:
                logging.debug("Error at strip 1: ", e)
                pass
            if one:
                try:
                    two = spt[1].strip()
                except Exception as e:
                    logging.debug("Error at strip 1: ", e)
                    two = ''
            else:
                pass

        if one and two:
            indict[one] = two
        else:
            pass

    return indict

def rtd2(string):
    logging.info("Converting RIS to dictionary ... (2)")
    indict = {}

    lines = string.splitlines()

    for i in lines:
        #print(i)
        spt = i.split('-', 1)
        try:
            one = spt[0].strip()
        except IndexError:
            pass
        if one:
            try:
                two = spt[1].strip()
            except IndexError:
                two = ''
        else:
            pass

        if one and two:
            indict[one] = two
        else:
            pass

    return indict


# parsing sources
def process_bibtex_onpage(q):
    r = requests.get(q)

    soup = BeautifulSoup(r.text, 'lxml')
    try:
        bibtex = soup.select("p")[0].get_text()
    except:
        pass

    if bibtex:
        bibdict = bibtexparser.loads(bibtex)
        item = bibdict.entries[0]
    else:
        item = "Not found"

    return item


def get_sources():
    return sources_dict


#this gives a name to the output dict
def build2(output, name):
    blam = {}

    if output != "Not found":
        blam[name] = output
    else:
        blam[name] = None

    return blam




# SEARCH FUNCTIONS

# ARTICLES
def doaj(result_queue, author='', title='', year='', doi='', isbn='', hit_limit = 10):
    #print("Searching doaj ...")
    logging.info("Searching doaj ...")
    count = 0

    # doi needs to be stripped
    if doi:
        query = 'doi:'+doi
    else:
        query = author+'%20'+str(year)+'%20'+title

    doaj_url = doaj_base+query
    iface_query = "https://doaj.org/search?ref=homepage-box&source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22"+query+"%22%2C%22default_operator%22%3A%22AND%22%7D%7D%7D"
    request = requests.get(doaj_url)
    data = request.json()

    for i in data['results']:
        i['bibjson']['rank'] = count
        i['bibjson']['type'] = 'article'
        i['bibjson']['query'] = iface_query

        count += 1


    hits = {'hits': []}
    hits['hits'] = data['results']
    result_queue.put(build2(hits, 'doaj'))
    return hits


def osf(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching osf ...")
    logging.info("Searching osf ...")
    count = 0

    if doi:
        query = '?q='+doi+'&type=preprint'
        #print request
    else:
        if len(author)>1:
            part2 = 'contributors:'+author
        else:
            part2 = ''

        if len(title)>1:
            part3 = 'title:'+title
        else:
            part3 = ''

        if len(year)>1:
            part4 = 'year:'+year
        else:
            part4 =''


        query = '?size='+str(hit_limit)+'&q='+part2+part3+part4

    osf_url = osf_base+query

    headers = {'Content-Type': 'application/json'}
    request = requests.get(osf_url, headers=headers)
    data = request.json()

    title2 = title.replace('+', ' ')


    try:
        data['status'] != "200"
        result_queue.put("Not found")
        return "Not found"
    except:
        data = data['hits']['hits']

        hits = {'hits': []}

        for i in data:
            i['_source']['rank'] = count
            i['_source']['landing_url'] = 'https://share.osf.io/preprint/'+i['_id']
            i['_source']['query'] = osf_url
            try:
                ls = []
                ls.append(url_constructor('landing', 'landing_url', i['_source']['identifiers'][0]))
                i['_source']['links'] =  ls
            except Exception as e:
                logging.debug('Issue with parsing data in osf(): ', e)
                pass

            count += 1
            hits['hits'].append(i['_source'])

        result_queue.put(build2(hits, 'osf'))
        return hits


def core(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    # print("Searching core ...")
    logging.info("Searching core ...")
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
                print(e)

            dl = suppchen.select_one('dl')

            subjects = dl.select('a[href*=subject_facet]')
            try:
                item['subjects'] = [s.get_text() for s in subjects]
            except Exception as e:
                #logging.debug('Extraction error in core(): ', e)
                pass
            try:
                item['type'] = dl.select_one('a[href*=genre_facet]').get_text()
            except Exception as e:
                #logging.debug('Extraction error in core(): ', e)
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
                #logging.debug('Error constructing urls in core(): ', e)
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

    result_queue.put(build2(hits, 'core'))
    return hits




def scielo(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    logging.info("Searching scielo ...")
    print("searching scielo")
    hits = {'hits': []}
    count = 0

    if doi:
        q = doi
    else:
        q = author+title+year

    query = scielo_base+q+"&lang=es&count=10&from=0&output=ris&sort=&format=summary&fb=&page=1"
    iface_query = "https://search.scielo.org/?lang=en&count=15&from=0&output=site&sort=&format=summary&fb=&page=1&q="+q

    ris = requests.get(query)
    bris = ris.text.split("ER  -")

    for i in bris[:-1]:
        mdata = rtd2(i)
        mdata['rank'] = count
        mdata['query'] = iface_query
        hits['hits'].append(mdata)
        count += 1

    result_queue.put(build2(hits, 'scielo'))
    return hits



def libgen_article(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching libgen_article ...")
    logging.info("Searching libgen_article ...")

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

        item['landing_url'] = libgen_home+'/'+tds[1].a.get('href')

        get_doi = tds[1].a.get('href').split("scimag/")[-1]
        get_title = tds[1].a.get_text()

        try:
            journal_data = tds[2].select('p')
            journal['name'] = journal_data[0].get_text()
            journal_info = re.findall(r'\d+', journal_data[1].get_text())
        except Exception as e:
            logging.debug("Error extractig journal info @libgen_article: ", e)

        try:
            journal['volume'] = journal_info[0]
        except Exception as e:
            logging.debug("Error extractig journal info @libgen_article: ", e)
        try:
            journal['issue'] = journal_info[1]
        except Exception as e:
            logging.debug("Error extractig journal info @libgen_article: ", e)

        try:
            journal['year'] = journal_info[2]
        except Exception as e:
            logging.debug("Error extractig journal info @libgen_article: ", e)

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

    result_queue.put(build2(hits, 'libgen_article'))
    return hits


# aka unpaywall
def oadoi(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    email = ""
    # print("Searching oadoi ...")
    logging.info("Searching oadoi ...")

    if doi:
        hits = {'hits': []}

        query = doi+'?email='+email
        query_url = oadoi_base+query

        request = requests.get(query_url)
        data = request.json()

        data['type'] = 'article'
        data['query'] = oadoi_base
        hits['hits'].append(data)
        result_queue.put(build2(hits, 'oadoi'))
        return hits

    else:
        result_queue.put(build2("Not found", 'oadoi'))
        return "Not found"


#BOOKS

def doab(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching doab ... ")
    logging.info("Searching doab ... ")

    count = 0

    #can search by ISBN
    if len(isbn) > 2:
        query = isbn
    else:
        query = author+'+'+title+'+'+year
        query = query.replace(' ', '+')

    doab_url = doab_base+query

    r = requests.get(doab_url)

    strain = SoupStrainer(id="result")
    soup = BeautifulSoup(r.text, "lxml", parse_only=strain)

    records = soup.select('div[id*="record"]')
    # print("how long: ", len(records))

    hits = {'hits': []}

    for i in records:
        try:
            gt_imag = i.select('img[src*="cover"]')
            img_href = gt_imag[0].get('src')
        except Exception as e:
            pass

        try:
            href = i.select("div#r1 > h1 > a:nth-of-type(3)")
            link = href[0].get('href')
        except Exception as e:
            pass

        try:
            get_mdata = i.select('a[href*="referenceManager"]')
            mlink = get_mdata[0].get('href')
        except Exception as e:
            pass

        try:
            ris = urllib.request.urlopen("https://www.doabooks.org"+mlink).readlines()
            mdata = rtd(ris)
        except Exception as e:
            pass

        try:
            tmp_href = 'http://www.doabooks.org'+link
            cons_href = url_constructor('download', 'download_url', tmp_href)
            mdata['href'] = cons_href
        except:
            pass

        try:
            mdata['img_href'] = 'http://www.doabooks.org'+img_href
        except:
            pass

        mdata['rank'] = count
        mdata['query'] = doab_url

        try:
            hits['hits'].append(mdata)
        except:
            pass

        count+=1

    result_queue.put(build2(hits, 'doab'))
    return hits



def oapen(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching OAPEN ...")
    logging.info("Searching oapen ...")

    author = author.replace(' ', '+')
    title = title.replace(' ', '+')
    query = 'creator='+author+'&title='+title+'&pubdate='+year+'&isbn='+isbn+'&doi='+doi+'&smode=advanced'

    oapen_url = oapen_base+query

    r = requests.get(oapen_url)
    strain = SoupStrainer('td',{'class': 'docHit'})
    soup = BeautifulSoup(r.text, 'lxml', parse_only=strain)
    links = soup.select('h3 a')

    hits = {'hits': []}
    count = 0

    for i in links:
        i = i.get('href').split('=')[1]
        gt_mdata = "http://oapen.org/download?type=export&export=ris&docid="+i
        r = urllib.request.urlopen(gt_mdata).readlines()
        mdata = rtd(r)
        mdata['rank'] = count
        slect = 'img[src*="'+i+'"]'
        gt_imag = soup.select(slect)
        more_hrefs = soup.select('a[href*="'+i+'"]')

        try:
            view = [url_constructor("open", "open_url", "http://oapen.org/"+m.get('href')) for m in more_hrefs if 'view' in m.get_text().lower()]
            mdata['links'] = view
        except Exception as e:
            logging.debug("Error constructing url in oapen(): ", e)

        try:
            img_href = gt_imag[0].get('src')
            mdata['img_href'] = "http://oapen.org"+img_href
        except Exception as e:
            pass

        mdata['query'] = oapen_url
        hits['hits'].append(mdata)
        count+=1

    try:
        result_queue.put(build2(hits, 'oapen'))
        return hits
    except Exception as e:
        result_queue.put(build2("Not found", 'oapen'))
        return "Not found"



def monoskop(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    # no isbn search
    # print("Searching Monoskop ...")
    logging.info("Searching monoskop ...")

    author = author.replace(' ','+')
    author = author.replace('\xa0', '+')
    title = title.replace(' ', '+')
    try:
        title = title.replace('”', '')
        title = title.replace('“', '')
    except:
        pass
    if len(isbn)>5:
        query = isbn
    else:
        query = author+'+'+title

    monoskop_url = monoskop_base+query

    request = urllib.request.Request(monoskop_url, headers={'User-Agent' : "Magic Browser"})

    con = urllib.request.urlopen(request)

    soup = BeautifulSoup(con)
    items = soup.select(".item")

    hits = {'hits': []}
    count = 0

    for i in items:
        print("item")

        mdata = {}

        title = i.select('h1')[0].get_text()
        landing = i.select('h1 a')[0].get('href')
        gt_imag = i.select('img')
        img_href = gt_imag[0].get('src')

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
        mdata['rank'] = count
        mdata['img_href'] = img_href
        mdata['desc'] = desc

        # problematic fields
        links.append(url_constructor('landing', 'landing_url', landing))
        mdata['href'] = links
        mdata['title'] = title

        mdata['query'] = monoskop_url

        mdata['isbn'] = isbns
        mdata['type'] = 'book'

        count+=1



        hits['hits'].append(mdata)


    try:
        result_queue.put(build2(hits, 'monoskop'))
    except Exception as e:
        result_queue.put(build2("Not found", 'monoskop'))
        return("Not found")



def libgen_book(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching libgen_book ...")
    logging.info("Searching libgen_book ...")

    global libgen_home
    hits = {'hits': []}
    count = 0

    if len(isbn)>8:
        try:
            hem = isbn.split(' ')
            isbn = hem[0]
        except:
            pass
        query = "isbn="+isbn+"&fields=*"
        libgen_books_url = libgen_base_books+query

        request = requests.get(libgen_books_url, headers={'Connection':'close'})
        logging.debug("ISBN based search results")
        data = request.json()

        # what happens to cover_url in this case?
        # delagate to update_libgen_json ... extends urls with domain names and classifies them
        try:
            good_links = update_libgen_json(data)
        except Exception as e:
            result_queue.put(build2("Not found", 'libgen_book'))
            return "Not found"

        # add rank
        for n in range(len(good_links)):
            good_links[n]['rank'] = n
            good_links[n]['query'] = libgen_books_url

        hits['hits'].append(good_links)

    else:
        q = author+'+'+title+'+'+year
        query = libgen_home+"/search.php?req="+q+"&open=0&res=25&view=detailed&phrase=1&column=def"

        r = requests.get(query)
        soup = BeautifulSoup(r.text, 'lxml')
        get_hrefs_init = soup.select('a[href*="index.php?md5"]')
        href_urls = update_libgen_src(libgen_home, get_hrefs_init, 'href')

        # set limit here ... lowest query = 25
        if len(href_urls)>hit_limit:
            get_hrefs = href_urls[:hit_limit]
        else:
            get_hrefs = href_urls

        # prepare links for processing
        new_hrefs = [libgen_base_books+"ids"+g.split('md5')[-1]+"&fields=*" for g in get_hrefs]

        with FuturesSession() as session:
            results = [session.get(g) for g in new_hrefs]

            for item in as_completed(results):
                record = item.result()

                # extends urls with domain names and classifies them
                # be careful data needs to be a list (or update_libgen_json needs to be upgraded)
                good_links = update_libgen_json(record.json())

                # add to the record
                good_links[0]['rank'] = count
                good_links[0]['query'] = query

                count+=1
                hits['hits'].append(good_links[0])

    result_queue.put(build2(hits, 'libgen_book'))
    return hits


def memoryoftheworld(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching memoryoftheworld ...")
    logging.info("Searching memoryoftheworld ...")

    url_authors = "#/search/authors/"
    url_title = "#/search/titles/"

    hits = {'hits': []}
    count = 0

    # it is actually less acurate if you remove ':'
    if len(author)>=2 and len(title)<=2:
        auth_prep = author.replace(' ', '+')
        query = url_authors+auth_prep
    elif len(title)>=2 and len(author)<=2:
        title_prep = title.replace(' ', '+')
        query = url_title+title_prep
    elif len(title)>=2 and len(author)>=2:
        title_prep = title.replace(' ', '+')
        query = url_title+title_prep
    else:
        result_queue.put(build2("Not found", 'memoryoftheworld'))
        return "Not found"


    if 'linux' in sys.platform:
    # start xvfb in case no X is running. Make sure xvfb
    # is installed, otherwise this won't work!
        dryscrape.start_xvfb()

    session = dryscrape.Session(base_url = memory_base)
    session.visit(query)

    try:
        session.wait_for_safe(lambda: session.at_xpath('/html/body/div/div[3]/div[2]/div[1]/div'))
    except Exception as e:
        logging.debug("Extraction error in memoryoftheworld(): ", e)
        out = build2("Not found", 'memoryoftheworld')
        result_queue.put(out)
        return out

    html = session.body()
    soup = BeautifulSoup(html, 'lxml')
    covers = soup.find_all("div", class_="card")

    if len(covers) < 1:
        result_queue.put(build2("Not found", 'memoryoftheworld'))
        return "No results"
    else:
        for i in covers[:hit_limit]:
            output = {}
            title_inner = i.select('div.card-title > span')[0].text.strip()
            landing = i.select_one('div.card-title > span > a')
            print("Landng ", landing)
            author_inner = i.select('div.card-subtitle > a')[0].text.strip()
            links = i.find_all('div', class_='card-text')
            cover_img = i.select('img.card-img')[0]['src']

            linksos = []
            hreff = links[0].children
            for i in hreff:
                try:
                    href = 'http:'+i['href']
                    text = i.text
                    link = dict({'href': href, 'format': text.lower()})
                    linksos.append(link)
                except:
                    pass

            output['author'] = author_inner
            output['title'] = title_inner
            output['rank'] = count
            output['href'] = linksos
            output['type'] = 'book'
            output['query'] = memory_base+query
            output['img_href'] = 'http:'+str(cover_img)
            hits['hits'].append(output)
            count += 1

    result_queue.put(build2(hits, 'memoryoftheworld'))
    return hits


# start of aaaaarg

# not really necessary when used run as flaskapp
def arglogin(username, password):
    url = "http://aaaaarg.fail/auth/login"
    session = Session()
    br = RoboBrowser(session=session, history=True, parser="lxml")
    br.open(url)
    form = br.get_forms()[1]
    form['email'].value = username
    form['password'].value = password
    br.submit_form(form)

    return br

def links2dicts(inhtml):
    links = []
    t = inhtml.find_all('a')
    for x in t:
        url = x.get('href')
        text = x.text
        one = {'desc':text , 'url': url}
        links.append(one)

    return links


def filter_lod(input_list, key, query):
    term = re.compile(query, re.IGNORECASE)
    allowed = [e for e in input_list if re.search(term, e[key])]
    return allowed



def getlink_arg(soup_material):
    output = {'link': []}
    soup = BeautifulSoup(soup_material, "lxml")
    try:
        x = soup.find('table', id='fileuploads')
    except Exception as e:
        logging.debug("No links found on thing page getlink_arg(): ", e)
        return output


    try:
        rows = x.find_all('tr')
    except Exception as e:
        return output

    for r in rows:

        tds = r.find_all('td')

        if tds:
            mustr = {'url': None, 'desc': None, 'mimetype': None, 'size': None}
            urls = links2dicts(tds[0])
            mustr['mimetype'] = tds[2].text
            mustr['size'] = tds[3].text
            mustr['url'] = aaaaarg_base+urls[0]['url']

            output['link'].append(mustr)

    return output




def get_maker_things_arg(soup_material):

    out = []
    strain = SoupStrainer('ul', class_="things unstyled")
    soup = BeautifulSoup(soup_material, 'lxml', parse_only=strain)
    lns = soup.select('a[href*="/thing"]')

    for r in lns:
        try:
            thing_url = r.get('href')
            thing_text = r.text
            one = {'thing_title': thing_text , 'thing_url': thing_url}
            out.append(one)
        except Exception as e:
            logging.debug("Error extracting maker links get_maker_things_arg(): ", e)
            pass

    return out




def getmakers_arg(soup_material, author):

    strain = SoupStrainer(id='things')
    soup = BeautifulSoup(soup_material, "lxml", parse_only=strain)

    chosen_makers = []
    makers = soup.find_all('li')

    if makers:
        for i in makers:
            if re.search(author, i.a.text, re.IGNORECASE):
                mt = i.a.text
                mh = i.a.get('href')
                out = {'author': mt, 'author_page_url': mh}
                chosen_makers.append(out)
            else:
                pass
    else:
        return "Not found"

    if len(chosen_makers)>=1:
        return chosen_makers
    else:
        return "Not found"



def parsearg(soup_material):
    output = []

    strain = SoupStrainer(id='fileuploads')
    soup = BeautifulSoup(soup_material, "lxml", parse_only=strain)

    hrefs = soup.find_all('a')
    for i in hrefs:
        if str(i.get('href')).startswith('/upload'):
            full = aaaaarg_base+str(i.get('href'))
            output.append(full)

        else:
            pass

    return output

def getthings_things_arg(soup_material, title):
    out = []
    strain = SoupStrainer(id='things')
    soup = BeautifulSoup(soup_material, "lxml", parse_only=strain)

    chosen_makers = []

    things = soup.find_all('li')

    for t in things:
        thing_href = t.find('a').get('href')
        thing_text = t.find('a').text

        miniout = {'title': thing_text, 'title_page_url': thing_href}
        out.append(miniout)

    return out


def getthing_metadata_arg(soup_material):

    logging.info("Additional metadata found aaaaarg")

    soup = BeautifulSoup(soup_material, "lxml")

    try:
        meta = soup.find('div', id='mdCollapse')
    except:
        pass

    if meta != None:
        meta_dict = {}
        lis = meta.find_all('li')
        for li in lis:
            one = {}
            if li.p:
                if li.p.text.startswith('[') or li.p.text.startswith('{'):
                    # this is a possibility [{u'key': u'/languages/eng'}]
                    # this too [1st American ed.] = problem
                    try:
                        one[li.strong.text] = ast.literal_eval(li.p.text)
                    except Exception as e:
                        pass
                    try:
                        meta_dict[li.strong.text] = ast.literal_eval(li.p.text)
                    except Exception as e:
                        logging.debug("Metadata extraciton error aaaaarg: ", e)
                        pass
                else:
                    meta_dict[li.strong.text] = li.p.text
            else:
                pass

    else:
        meta_dict = {}
        author_as = soup.select('h5 > ul > a')

        try:
            one_author = author_as[0]
        except Exception as e:
            return meta_dict

        titl_tmp = {'title': None}
        get_titl = soup.find('title')
        meta_dict['title'] = get_titl.text

        if len(author_as) > 1:
            author_ish = {'author': []}
            for a in author_as:
                author_ish['author'].append(a.text)

            desc = soup.find('p', {'class': 'lead'})

            meta_dict['author'] = author_ish['author']
            meta_dict['desc'] = desc.text
        else:

            desc = soup.find('p', {'class': 'lead'})
            try:
                meta_dict['desc'] = desc.text
            except Exception as e:
                logging.debug("Metadata extraciton error aaaaarg - desc: ", e)
            try:
                meta_dict['author'] = author_as[0].a.text
            except Exception as e:
                logging.debug("Metadata extraciton error aaaaarg - author: ", e)


    return meta_dict


# aaaaarg controller function
def aaaaarg(result_queue, br, author='', title='', hit_limit=10):
    #print("Searching aaaaarg ...")
    logging.info("Searching aaaaarg ...")
    # if troo it will loop through all the pages
    loop = False

    hits = {'hits': []}

    # three types of query procedures depending on query fields
    if len(author) > 2 and len(title) < 2:
        query = aaaaarg_makers_base+author

        try:
            br.open(query)
        except Exception as e:
            logging.debug("Aaaaarg login failure ...")
            return "Not found"

        makers = br.select('html')
        makers = str(makers[0])

        authorpage = getmakers_arg(makers, author)
        #print(len(authorpage))

        if authorpage == "Not found":
            return authorpage
        else:
            for a in authorpage[:3]:
                br.open(aaaaarg_base+a['author_page_url'])

                things = br.select('html')

                things = str(things[0])
                thing_links = get_maker_things_arg(things)

                if thing_links == "Not found":
                    return thing_links
                else:
                    # balance the number of hits per maker/author
                    if len(authorpage) == 1:
                        thing_limit = 10
                    elif len(authorpage) == 2:
                        thing_limit = 5
                    else:
                        thing_limit = 3

                    for t in thing_links[:thing_limit]:
                        br.open(aaaaarg_base+t['thing_url'])
                        files = br.select('html')
                        files = str(files[0])

                        links = getlink_arg(files)
                        landing = aaaaarg_base+t['thing_url']
                        mdata = getthing_metadata_arg(files)

                        # combine before appending
                        links['link'].append({'type': 'landing_url', 'name': 'landing', 'href': landing})
                        mdata['query'] = query
                        mdata['links'] = links['link']
                        hits['hits'].append(mdata)



    elif len(title) > 2 and len(author) < 2:
        pagecount = 1
        # there's pages upon pages of results!! "ends" when id=things is very short indeed ... or when it contains no li
        #url = "https://aaaaarg.fail/search/things?query=software&page=27"

        if loop == True:
            while pagecount:
                query = aaaaarg_things_base+title+"&page="+str(pagecount)

                try:
                    br.open(query)
                except Exception as e:
                    logging.debug("Aaaaarg login failure ...")
                    return "Not found"

                sm = br.select('html')
                things = str(sm[0])
                strain = SoupStrainer(id='things')
                soup = BeautifulSoup(things, parse_only=strain)
                li = soup.find_all('li')

                if  len(li) < 1:
                    break
                else:
                    thing_links = getthings_things_arg(things, title)

                    for t in thing_links:
                        landing = aaaaarg_base+t['title_page_url']
                        br.open(landing)
                        h = br.select('html')
                        hin = str(h[0])

                        links = getlink_arg(hin)

                        mdata = getthing_metadata_arg(hin)

                        # combine these two before appending
                        links['link'].append({'type': 'landing_url', 'name': 'landing', 'href': landing})
                        mdata['query'] = query
                        mdata['links'] = links['link']
                        hits['hits'].append(mdata)

                pagecount+=1

        # partial repetition of the code above ... put inside a function
        else:
            query = aaaaarg_things_base+title

            try:
                br.open(query)
            except Exception as e:
                logging.debug("Aaaaarg login failure ...")
                return "Not found"

            sm = br.select('html')
            things = str(sm[0])
            strain = SoupStrainer(id='things')
            soup = BeautifulSoup(things, parse_only=strain)
            li = soup.find_all('li')

            if len(li) < 1:
                return "Not found"
            else:
                thing_links = getthings_things_arg(things, title)

                for t in thing_links:
                    landing = aaaaarg_base+t['title_page_url']

                    br.open(landing)
                    h = br.select('html')
                    hin = str(h[0])

                    links = getlink_arg(hin)
                    mdata = getthing_metadata_arg(hin)

                    links['link'].append({'type': 'landing_url', 'name': 'landing', 'href': landing})
                    mdata['query'] = query

                    if len(links['link']) >= 1:
                        mdata['links'] = links['link']

                    hits['hits'].append(mdata)

            pagecount+=1


    elif len(title) > 2 and len(author) > 2:
        query = aaaaarg_makers_base+author

        try:
            br.open(query)
        except Exception as e:
            logging.debug("Aaaaarg login failure ...")
            return "Not found"

        makers = br.select('html')
        makers = str(makers[0])
        authorpage = getmakers_arg(makers, author)

        if authorpage == "Not found":
            return authorpage
        else:
            br.open(aaaaarg_base+authorpage[0]['author_page_url'])

            things = br.select('html')
            things = str(things[0])
            thing_links = get_maker_things_arg(things)

            tlf = filter_lod(thing_links, 'thing_title', title)

            for t in tlf:

                br.open(aaaaarg_base+t['thing_url'])
                ahem = str(br.select('html')[0])

                links = getlink_arg(ahem)
                mdata = getthing_metadata_arg(ahem)

                mdata['author'] = author
                links['link'].append({'type': 'landing_url', 'name': 'landing', 'href': landing})
                mdata['query'] = query
                mdata['links'] = links['link']
                hits['hits'].append(mdata)


    else:
        result_queue.put(build2("Not found", 'aaaaarg'))
        return "Not found"


    if hits:
        count = 0
        for h in hits['hits']:
            h['rank'] = count
            count+=1
        result_queue.put(build2(hits, 'aaaaarg'))
        return hits
    else:
        result_queue.put(build2("Not found", 'aaaaarg'))
        return "Not found"


# end of aaaaarg


# debug
def debug_pileup(author='', title='', year='', doi='', isbn=''):
    hits = {"hits": []}
    a = {"title": "help", "annote": "what is happening here"}
    b = {"title": "i neéd somebody", "annote": "i hope tis something i can understand"}
    hits['hits'].append(a)
    hits['hits'].append(b)

    return hits




# CONTROLLER FUNCTIONS

# without multiprocessing
def combined(author='', title='', year='', doi='', isbn='', sources='', hit_limit=10):

    results = []
    # print("Selected sources ", sources)
    # for i in sources:
    #     print(sources_short[i])

    for i in sources:
        if i == 5:
            print("Logging into AAAAARG now ...")
            br = arglogin(aaaaarg_username, aaaaarg_password)
            print("Logged in successfully.")
            output = aaaaarg(br, author, title)

            stuff = build2(output, str(sources_short[i]))
            results.append(stuff)
        else:
            func_name = sources_short[i]
            possibles = globals().copy()
            possibles.update(locals())
            func = possibles.get(func_name)
            output = func(author, title, year, doi, isbn, hit_limit)

            stuff = build2(output, str(sources_short[i]))
            results.append(stuff)

    return results


# with multiprocessing
def new_combined(author='', title='', year='', doi='', isbn='', sources='', hit_limit=10, aaaaarg_browser=None):

    selection = [n['code_name'] for n in sources_dict if n['id'] in sources]

    possibles = globals().copy()
    possibles.update(locals())

    result_queue = Queue()
    proc = []
    results = []

    for fn in selection:
        # special treatment for aaaaarg is necessary because of different parameters
        if fn == 'aaaaarg':
            p = Process(target=possibles.get(fn), args=(result_queue, aaaaarg_browser, author, title, hit_limit))
        else:
            p = Process(target=possibles.get(fn), args=(result_queue, author, title, year, doi, isbn, hit_limit))

        p.start()
        proc.append(p)

    # pull the data out of the queue before the join
    for p in proc:
        item = result_queue.get()
        results.append(item)

    for p in proc:
        p.join()

    return results



# main search functoins, runs combined or new_combined
def search(author='', title='', year='', doi='', isbn='', sources='', aaaaarg_browser=None):
    print("RADOVAN SEARCHING ...")

    output_dict = {'entries': []}
    global global_hit_limit

    def make_output_dict(results):
        for i in results:
            output_dict['entries'].append(i)

        return output_dict

    try:
        sources = sources.split(' ')
    except:
        pass

    if isinstance(sources, list):
        if is_number(sources[0]):
            pass
        else:
            tmp = []
            for s in sources:
                num = [n['id'] for n in sources_dict if n['code_name'] == s]
                tmp.append(num[0])
            sources = tmp
    elif sources == None:
        sources = themall
    else:
        pass

    # remove aaaarg from list of sources if login unsuccessful
    if aaaaarg_browser == None and 5 in sources:
        sources.remove(5)

    rslt = new_combined(author=author, title=title, year=year, doi=doi, isbn=isbn, sources=sources, hit_limit=10, aaaaarg_browser=aaaaarg_browser)

    for r in rslt:
        output_dict['entries'].append(r)

    return output_dict
