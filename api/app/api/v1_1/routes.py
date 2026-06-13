import cProfile
import io
import pstats
from json import dumps

from flask import request, jsonify, make_response, Blueprint

# TO DO: absolute imports pls
from app.bibjson_methods.methods import mein_main
from app.core.radovan_core_flexi import search
from app.core.radovan_core_flexi import get_sources
from app.validators import validate_parameters


api_1_1 = Blueprint("api_1_1", __name__)


# TO DO: this is unnecessary
def jsonify(dictoner, status=200, indent=4, sort_keys=True):
  response = make_response(dumps(dictoner, indent=indent, sort_keys=sort_keys))
  response.headers['Content-Type'] = 'application/json; charset=utf-8'
  response.headers['mimetype'] = 'application/json'
  response.status_code = status
  return response

# TO DO: this is utils
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# TO DO: separate this
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


# BASE
@api_1_1.route("/v1.1/", methods=["GET"])
def hello_world():
    hlo = {
        "hello": "Hello, World! This is Radovan. The API is running at /radovan/api/",
        "version_info": "The current version is 1.1. For information on the previous version go to /radovan/api/v1.0",
        "endpoint": [
            "/search/single for single queries",
            "/search/bulk for bulk queries",
        ],
        "parameters": "author, title, year, doi, isbn, sources",
        "sample_queries": [
            "/radovan/api/search/single?author=miller&title=&year=2010&isbn=&doi=&sources=2+3",
            "/radovan/api/search/single?author=miller&title=&year=2010&isbn=&doi=&sources=2&sources=3",
        ],
    }
    return hlo


# SEARCH
@api_1_1.route("/v1.1/search/single", methods=["GET"])
def search_one():

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


# BULK SEARCH (input bibjson)
@api_1_1.route('/v1.1/search/bulk')
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



# RETURN SOURCES
@api_1_1.route('/v1.1/sources')
def rsources_two():
    all = get_sources()
    return jsonify(all)
