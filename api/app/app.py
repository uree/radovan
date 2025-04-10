# -*- coding: utf-8 -*-
# python 3.6.9
import cProfile
import io
import logging
import pprint
import pstats
from json import dumps

from flask import Flask, request, jsonify, make_response
from requests import Session
from robobrowser import RoboBrowser

from bibjson_methods.methods import mein_main
from core.keys import *
from logs.setup import setup_logging
from core.radovan_core_flexi import search
from core.radovan_core_flexi import get_sources
from validators import validate_parameters


app = Flask(__name__)
app.config['RESTFUL_JSON'] = {'ensure_ascii': False}

setup_logging()
app.logger = logging.getLogger(__name__)
app.logger.info("Error logging works.")

pp = pprint.PrettyPrinter(indent=4)

try:
    aaaaarg_username = yarr_user
    aaaaarg_password = yarr_pass
except:
    aaaaarg_username = None
    aaaaarg_password = None


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
@app.route('/')
def hello_world_current():
    hello = "Hello, World! This is Radovan. The API is running at /radovan/api/"
    version = "The current version is 1.1. For information on the previous version go to /radovan/api/v1.0"
    endpoint = ["/search/single for single queries", '/search/bulk for bulk queries']
    parameters = "author, title, year, doi, isbn, sources"
    sample_query = "/radovan/api/search/single?author=miller&title=&year=2010&isbn=&doi=&sources=2+3 or /radovan/api/search/single?author=miller&title=&year=2010&isbn=&doi=&sources=2&sources=3"
    hlo = {'hello': hello, 'version_info': version, 'endpoint': endpoint, 'parameters': parameters, 'sample_query': sample_query}
    return hlo


@app.route('/v1.0')
def hello_world():
    # app.flogger.info("hello")
    app.logger.debug("hello both ways")
    hello = "Hello, World! This is Radovan. The API is running at /radovan/api/v1.0/"
    endpoint = ["/simple for single queries", '/bulk for bulk queries']
    parameters = "author, title, year, doi, isbn, sources"
    sample_query = ""
    hlo = {'hello': hello, 'endpoint': endpoint, 'parameters': parameters, 'sample_query': sample_query}
    return jsonify(hlo)


# SEARCH
@app.route('/search/single')
def search_one():
    try:
        global aaaaarg_browser
    except:
        aaaaarg_browser = None

    arguments = validate_parameters(request.args)

    if arguments['valid_query'] == False:
        return arguments

    # accept two source listing formats here
    rargs = request.args.to_dict(flat=False)

    try:
        # &sources=2&sources=3
        sources_int = [int(n) for n in rargs['sources']]
    except:
        # sources=1+2+3+4+5+6+7+8+9+10+11+12
        sources_int = [int(n) for n in rargs['sources'][0].split()]

    simple_results = search(rargs['author'][0], rargs['title'][0], rargs['year'][0], rargs['doi'][0], rargs['isbn'][0], sources_int)

    nice_output = mein_main(simple_results)

    nice_output_sorted = sorted(nice_output['hits'], key=lambda k: k['extra'][0]['rank'])

    nice_dict = {'hits': nice_output_sorted, 'meta': {'number_of_hits': len(nice_output_sorted), 'hits_per_source': nice_output['meta']['hits_per_source']}}

    return nice_dict


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

        # TRANSFORM TO BIBJSON
        #print("------------------- FORMATTING DATA ---------------------")
        nice_output = mein_main(simple_results)


        nice_output_sorted = sorted(nice_output['hits'], key=lambda k: k['extra'][0]['rank'])
        #print("nice output sorted")
        #pp.pprint(nice_output_sorted)
        return jsonify(nice_output_sorted)


# BULK SEARCH (input bibjson)
@app.route('/search/bulk')
def search_bulk():
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
        return error

    # this should be executed in parallel (quasi), no?
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
            pass

        results_combined['bib_and_links'].append(temp)

    results_combined['total_number_links'] = links_total
    results_combined['references_with_new_links'] = refs_with_hits

    return jsonify(results_combined)
    return "bulk search"


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
        return error

    # this should be executed in parallel (quasi), no?
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
        if len(nice_output['hits']) >= 1:
            refs_with_hits += 1
            links_total += len(nice_output)


        # rank by rank
        try:
            temp['search_results'] = sorted(nice_output['hits'], key=lambda k: k['extra'][0]['rank'])
        except Exception as e:
            pass

        results_combined['bib_and_links'].append(temp)


    results_combined['total_number_links'] = links_total
    results_combined['references_with_new_links'] = refs_with_hits

    return jsonify(results_combined)


# RETURN SOURCES
@app.route('/sources')
def rsources_two():
    all = get_sources()
    return jsonify(all)


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
    # en/dis-able aaaaarg
    aaaaarg_username = None
    aaaaarg_password = None

    if aaaaarg_username and aaaaarg_password:
        aaaaarg_browser = arglogin(aaaaarg_username, aaaaarg_password)
    else:
        aaaaarg_browser = None

    app.run(host ='0.0.0.0', port = 9003, debug=True)
