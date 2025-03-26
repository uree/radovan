import logging
import requests

from fixing_links import url_constructor

logger = logging.getLogger(__name__)
osf_base = 'https://share.osf.io/api/v2/search/creativeworks/_search'


def osf(result_queue, author='', title='', year='', doi='', isbn='', hit_limit=10):
    #print("Searching osf ...")
    logger.info("Searching osf ...")
    count = 0

    hits = {'hits': []}

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
        result_queue.put({'osf': hits})
        return {'osf': hits}
    except:
        data = data['hits']['hits']


        for i in data:
            i['_source']['rank'] = count
            i['_source']['landing_url'] = 'https://share.osf.io/preprint/'+i['_id']
            i['_source']['query'] = osf_url
            try:
                ls = []
                ls.append(url_constructor('landing', 'landing_url', i['_source']['identifiers'][0]))
                i['_source']['links'] =  ls
            except Exception as e:
                logger.debug('Issue with parsing data in osf(): ', e)
                pass

            count += 1
            hits['hits'].append(i['_source'])

        result_queue.put({'osf': hits})
        return {'osf': hits}
