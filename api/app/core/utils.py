import io
import logging
import pstats
import requests
import re

import bibtexparser
import cProfile
from bs4 import BeautifulSoup

from fixing_links import url_constructor

logger = logging.getLogger(__name__)


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
            #print("no original links for "+entry['title'])
            #return None
            pass
    else:
        try:
            entry['url'] = ''
        except IndexError:
            pass

# ris to dict
def rtd(string):
    logger.info("Converting RIS to dictionary ... (1)")
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
                logger.debug("Error at split: ", e)
                pass

            try:
                one = spt[0].strip()
            except Exception as e:
                logger.debug("Error at strip 1: ", e)
                pass
            if one:
                try:
                    two = spt[1].strip()
                except Exception as e:
                    logger.debug("Error at strip 1: ", e)
                    two = ''
            else:
                pass

        if one and two:
            indict[one] = two
        else:
            pass

    return indict

def rtd2(string):
    logger.info("Converting RIS to dictionary ... (2)")
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
