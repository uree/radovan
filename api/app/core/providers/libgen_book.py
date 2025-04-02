import logging
import requests

from bs4 import BeautifulSoup

from .utils import fetch_provider


logger = logging.getLogger(__name__)
libgen_home = 'https://libgen.is'
libgen_base_books = libgen_home+"/json.php?"


def update_libgen_json(data):
    current_libgen_ip = "https://download.books.ms/main/"
    for_cover = "https://download.books.ms/covers/"

    tmp = []

    for d in data:
        cover_url = for_cover+d['coverurl']
        magic_number = d['coverurl'].split('/')[0]

        # generate download url
        download_url = current_libgen_ip+magic_number+'/'+d['md5']+'/'+d['locator']

        # update
        d['coverurl'] = cover_url
        mini_locator = {'type': 'landing_url', 'href': download_url, 'name': 'landing'}
        d['locator'] = mini_locator
        d['landing_url'] = libgen_home+'/book/index.php?md5='+d['md5']
        tmp.append(d)

    return tmp


def update_libgen_src(libgen_home, lst, target):
    srcs = [libgen_home+l.get(target).replace('..','') for l in lst]
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
    count = 0
    hits = []

    soup = BeautifulSoup(results, 'lxml')
    get_hrefs_init = soup.select('a[href*="index.php?md5"]')
    href_urls = update_libgen_src(libgen_home, get_hrefs_init, 'href')

    # set limit here ... lowest query = 25
    if len(href_urls) > hit_limit:
        get_hrefs = href_urls[:hit_limit]
    else:
        get_hrefs = href_urls

    # prepare links for processing
    new_hrefs = [libgen_base_books+"ids"+g.split('md5')[-1]+"&fields=*" for g in get_hrefs]

    for hr in new_hrefs:
        record = requests.get(hr).json()

        # extends urls with domain names and classifies them
        # be careful data needs to be a list (or update_libgen_json needs to be upgraded)
        try:
            good_links = update_libgen_json(record)
        except Exception as e:
            logger.debug(e)
            good_links = [{'error': 'libgen record parsing error'}]

        # add to the record
        good_links[0]['rank'] = count
        good_links[0]['query'] = query
        count += 1
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

    if len(isbn) > 8:
        try:
            hem = isbn.split(' ')
            isbn = hem[0]
        except Exception as e:  # noqa
            pass
        query = "isbn="+isbn+"&fields=*"
        libgen_books_url = libgen_base_books+query
        headers = {"Connection": "close"}
        format = "json"

    else:
        query = author+'+'+title+'+'+year
        libgen_books_url = libgen_home+"/search.php?req="+query+"&open=0&res=25&view=detailed&phrase=1&column=def"  # noqa:501
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
