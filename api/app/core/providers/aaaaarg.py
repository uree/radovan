import ast
import logging
import re
from requests import Session

from bs4 import BeautifulSoup, SoupStrainer
from robobrowser import RoboBrowser


logger = logging.getLogger(__name__)
aaaaarg_search_base = 'http://aaaaarg.fail/search?query='
aaaaarg_makers_base = 'http://aaaaarg.fail/search/makers?query='
aaaaarg_things_base = 'https://aaaaarg.fail/search/things?query='
aaaaarg_base = 'http://aaaaarg.fail'
aaaaarg_username = ""
aaaaarg_password = ""


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
        logger.debug("No links found on thing page getlink_arg(): ", e)
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
            logger.debug("Error extracting maker links get_maker_things_arg(): ", e)
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

    logger.info("Additional metadata found aaaaarg")

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
                        logger.debug("Metadata extraciton error aaaaarg: ", e)
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
                logger.debug("Metadata extraciton error aaaaarg - desc: ", e)
            try:
                meta_dict['author'] = author_as[0].a.text
            except Exception as e:
                logger.debug("Metadata extraciton error aaaaarg - author: ", e)


    return meta_dict


# aaaaarg controller function
def aaaaarg(result_queue, br, author='', title='', hit_limit=10):
    #print("Searching aaaaarg ...")
    logger.info("Searching aaaaarg ...")
    # if troo it will loop through all the pages
    loop = False

    hits = {'hits': []}

    # three types of query procedures depending on query fields
    if len(author) > 2 and len(title) < 2:
        query = aaaaarg_makers_base+author

        try:
            br.open(query)
        except Exception as e:
            logger.debug("Aaaaarg login failure ...")
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
                    logger.debug("Aaaaarg login failure ...")
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
                logger.debug("Aaaaarg login failure ...")
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
            logger.debug("Aaaaarg login failure ...")
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
        result_queue.put({'aaaaarg': hits})
        return {'aaaaarg': hits}


    if hits:
        count = 0
        for h in hits['hits']:
            h['rank'] = count
            count+=1

    result_queue.put({'aaaaarg': hits})
    return {'aaaaarg': hits}
