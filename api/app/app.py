# -*- coding: utf-8 -*-
# python 3.6.9

from flask import Flask, request, jsonify, make_response
from json import dumps
from radovan_core_flexi import search
from radovan_core_flexi import get_sources
from bibjson_methods import mein_main
import pprint
import cProfile, pstats, io

from robobrowser import RoboBrowser
from requests import Session

import logging

app = Flask(__name__)
app.config['RESTFUL_JSON'] = { 'ensure_ascii': False }

logging.basicConfig(filename='logs/radovan_api_log.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
pp = pprint.PrettyPrinter(indent=4)

aaaaarg_username = ""
aaaaarg_password = ""

def jsonify(dictoner, status=200, indent=4, sort_keys=True):
  response = make_response(dumps(dictoner, indent=indent, sort_keys=sort_keys))
  response.headers['Content-Type'] = 'application/json; charset=utf-8'
  response.headers['mimetype'] = 'application/json'
  response.status_code = status
  return response

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

# PROFILING, TIMING
def profile(fnc):

    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        # ... do something ...
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return inner

# AAAAARG
def arglogin(username, password):
    url = "http://aaaaarg.fail/auth/login"
    session = Session()
    br = RoboBrowser(session=session, history=True, parser="lxml")
    br.open(url)
    #print(br)
    try:
        form = br.get_forms()[1]
    except:
        return None

    form['email'].value = username
    form['password'].value = password
    br.submit_form(form)

    return br



# BASE
@app.route('/v1.0')
def hello_world():
    hello = "Hello, World! This is Radovan. The API is running at /radovan/api/v1.0/"
    endpoint = ["/simple for single queries", '/bulk for bulk queries']
    parameters = "author, title, year, doi, isbn, sources"
    sample_query = ""
    hlo = {'hello': hello, 'endpoint': endpoint, 'parameters': parameters, 'sample_query': sample_query}
    return jsonify(hlo)

# SEARCH
@app.route('/v1.0/simple/items')
def simple():
    try:
        global aaaaarg_browser
    except:
        aaaaarg_browser = None

    author  = request.args.get('author', '')
    title  = request.args.get('title', '')
    year = request.args.get('year', '')
    doi = request.args.get('doi', '')
    isbn = request.args.get('isbn', '')
    sources = request.args.get('sources', None)
    #print(sources)
    sources_int = [int(n) for n in sources.split()]
    #print(sources_int)
    if len(author)<1 and len(title)<1 and len(year)<1 and len(doi)<1 and len(isbn)<1:
        return jsonify({'response': 'incorrect query format', 'sample_query': '/v1.0/simple/items?author=foucault&title=society&year=&isbn=&doi=&sources=0+1+2+3'})
    else:
        simple_results = search(author, title, year, doi, isbn, sources_int)
        #print("------------------- END CORE FLEXI ---------------------")
        logging.info("---- end core flexi ----")

        # TRANSFORM TO BIBJSON
        #print("------------------- FORMATTING DATA ---------------------")
        nice_output = mein_main(simple_results)
        nice_output_sorted = sorted(nice_output, key=lambda k: k['extra'][0]['rank'])
        pp.pprint(nice_output_sorted)
        return jsonify(nice_output_sorted)


# BULK SEARCH (input bibjson)
@app.route('/v1.0/bulk', methods=['GET', 'POST'])
def bulk():
    error = jsonify({'response': 'incorrect query format'})

    # set range of sources for query
    all_sources = get_sources()
    source_ids = [n['id'] for n in all_sources]

    data = request.json

    # accounting
    refs_with_hits = 0
    links_total = 0

    try:
        results_combined = {'references_with_new_links': None, 'total_references': len(data), 'total_number_links': None, 'bib_and_links': []}
    except Exception as e:
        logging.debug("Error generating results: ", e)
        return error

    # this needs to be executed in parallel (quasi)
    for ref in data:
        #print("#### NEXT REF ####")
        temp = ref
        try:
            author = ref['bibjson'][0]['author'][0]['name']
        except Exception as e:
            author = ''
            pass

        try:
            title = ref['bibjson'][0]['title']
        except Exception as e:
            title = ''
            pass

        try:
            year = ref['bibjson'][0]['year']
        except Exception as e:
            year = ''
            pass

        try:
            if ref['bibjson'][0]['identifier'][0]['type'].lower() == 'doi':
                doi = ref['bibjson'][0]['identifier'][0]['id']
                #print(doi)
            else:
                doi = ''
        except Exception as e:
            #print(e)
            doi = ''
            pass

        try:
            if ref['bibjson'][0]['identifier'][0]['type'].lower() == 'isbn':
                isbn = ref['bibjson'][0]['identifier'][0]['id']
                #print(isbn)
            else:
                isbn = ''
        except Exception as e:
            #print(e)
            isbn = ''
            pass

        # search
        simple_results = search(author, title, year, doi, isbn, source_ids)

        # standardize results
        nice_output = mein_main(simple_results)

        #register that the reference has at least 1 new link
        if len(nice_output) >= 1:
            refs_with_hits += 1
            links_total += len(nice_output)


        # rank by rank
        try:
            temp['search_results'] = sorted(nice_output, key=lambda k: k['extra'][0]['rank'])
        except Exception as e:
            logging.debug("Error while sorting results: ", e)
            pass

        results_combined['bib_and_links'].append(temp)


    results_combined['total_number_links'] = links_total
    results_combined['references_with_new_links'] = refs_with_hits

    return jsonify(results_combined)


# RETURN SOURCES
@app.route('/v1.0/sources')
def rsources():
    all = get_sources()
    return jsonify(all)

@app.route('/v1.0/sources/<string:key>/<value>')
def frsources(key, value):
    all = get_sources()
    if is_number(value):
        value = int(value)
    ftr = [a for a in all if a[key] == value]
    return jsonify(ftr)

if __name__ == '__main__':
    aaaaarg_browser = arglogin(aaaaarg_username, aaaaarg_password)
    if aaaaarg_browser != None:
        logging.info("Login successful.")
    else:
        logging.info("Aaaaarg login failed.")

    app.run(host ='0.0.0.0', port = 9003)
