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


api_1_0 = Blueprint("api_1_0", __name__)


@api_1_0.route('/v1.0/simple/items')
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


@api_1_0.route('/v1.0/bulk', methods=['GET', 'POST'])
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


@api_1_0.route('/v1.0/sources')
def rsources():
    all = get_sources()
    return jsonify(all)


@api_1_0.route('/v1.0/sources/<string:key>/<value>')
def frsources(key, value):
    all = get_sources()
    if is_number(value):
        value = int(value)
    ftr = [a for a in all if a[key] == value]
    return jsonify(ftr)