import logging
import requests

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
libgen_home = 'https://libgen.is'
libgen_base_books = libgen_home+"/json.php?"


def update_libgen_json(data):
    current_libgen_ip = "http://31.42.184.140/main/"
    for_cover = "http://31.42.184.140/covers/"
    current_libgen_home = "http://libgen.unblocked.name"

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
        d['landing_url'] = current_libgen_home+'/book/index.php?md5='+d['md5']
        tmp.append(d)

    return tmp


def update_libgen_src(libgen_home, lst, target):
    srcs = [libgen_home+l.get(target).replace('..','') for l in lst]
    return srcs


def libgen_book(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    logger.info("Searching libgen_book ...")

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
        logger.debug("ISBN based search results")
        try:
            data = request.json()
        except ValueError as e:
            logger.error("Value error isbn search libgen book")
            result_queue.put({'libgen_book': hits})
            return {'libgen_book': hits}


        if len(data) != 0:
            # what happens to cover_url in this case?
            # delagate to update_libgen_json ... extends urls with domain names and classifies them
            try:
                good_links = update_libgen_json(data)
            except Exception as e:
                good_links = None


            # add rank
            if good_links != None:
                for n in range(len(good_links)):
                    good_links[n]['rank'] = n
                    good_links[n]['query'] = libgen_books_url

                hits['hits'] = good_links
            else:
                result_queue.put({'libgen_book': hits})
                return {'libgen_book': hits}


    else:
        q = author+'+'+title+'+'+year
        query = libgen_home+"/search.php?req="+q+"&open=0&res=25&view=detailed&phrase=1&column=def"

        r = requests.get(query)
        soup = BeautifulSoup(r.text, 'lxml')
        #print("libgen_book_soup")
        #print(soup)
        get_hrefs_init = soup.select('a[href*="index.php?md5"]')
        href_urls = update_libgen_src(libgen_home, get_hrefs_init, 'href')

        # set limit here ... lowest query = 25
        if len(href_urls)>hit_limit:
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

            count+=1
            hits['hits'].append(good_links[0])

    result_queue.put({'libgen_book': hits})
    return {'libgen_book': hits}
