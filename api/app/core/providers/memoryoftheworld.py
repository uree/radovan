import logging
import requests


logger = logging.getLogger(__name__)
memory_base = 'https://library.memoryoftheworld.org/'


def memoryoftheworld(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    # this is the api version
    logger.info("Searching memoryoftheworld ...")

    url_authors = "https://library.memoryoftheworld.org/search/authors/"
    url_title = "https://library.memoryoftheworld.org/search/title/"
    url_isbn = "https://library.memoryoftheworld.org/search/_isbn/"

    hits = {'hits': []}
    count = 0

    # it is actually less acurate if you remove ':'
    if len(isbn)>2:
        isbn_prep = isbn.strip().replace('-', '')
        query = url_isbn+isbn_prep
    elif len(author)>=2 and len(title)<=2:
        auth_prep = author.replace(' ', '+')
        query = url_authors+auth_prep
    elif len(title)>=2 and len(author)<=2:
        title_prep = title.replace(' ', '+')
        query = url_title+title_prep
    elif len(title)>=2 and len(author)>=2:
        title_prep = title.replace(' ', '+')
        query = url_title+title_prep
    else:
        result_queue.put({'memoryoftheworld': hits})
        return {'memoryoftheworld': hits}

    logger.debug(query)

    try:
        r = requests.get(query, verify=False) # ssl
        data = r.json()
    except requests.exceptions.SSLError:
        data = {"_items": []}

    if len(data['_items']) > 0:

        for i in data['_items'][:hit_limit]:
            output = {}
            url_base = 'https:'+i['library_url']
            linksos = []

            for f in i['formats']:
                try:
                    href = url_base+f['dir_path']+f['file_name']
                    text = f['format']
                    link = dict({'href': href, 'format': text.lower()})
                    linksos.append(link)
                except:
                    pass

            output['author'] = [n for n in i['authors']]
            output['title'] = i['title']
            output['rank'] = count
            output['href'] = linksos
            output['type'] = 'book'
            output['query'] = query
            output['img_href'] = url_base+i['cover_url']
            hits['hits'].append(output)
            count += 1

    logger.debug(hits)

    result_queue.put({'memoryoftheworld': hits})
    return {'memoryoftheworld': hits}
