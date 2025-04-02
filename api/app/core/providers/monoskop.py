import logging
import re

import urllib
from bs4 import BeautifulSoup

from fixing_links import url_constructor


logger = logging.getLogger(__name__)
monoskop_base = 'https://monoskop.org/log/?cat=17&s='


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
    count = 0

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

    monoskop_url = monoskop_base+query

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

    for i in items:
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

        count += 1

        hits['hits'].append(mdata)

    result_queue.put({'monoskop': hits})
    return {'monoskop': hits}
