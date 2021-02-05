# -*- coding: utf-8 -*-
# python 3.6.9

import requests
import json
from flask import Flask, request, jsonify, make_response, render_template
import collections
import pprint
import logging


app = Flask(__name__)
app.config['RESTFUL_JSON'] = { 'ensure_ascii': False }

logging.basicConfig(filename='logs/radovan_iface_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
pp = pprint.PrettyPrinter(indent=4)

# get sources and select all
# global sources_d
# r = requests.get('http://localhost:9003/v1.0/sources').json()
#
# for item in r:
#     item.update({"selected": 1})
#
# sources_d = r

@app.route('/')
def search():
    sources_d = requests.get('http://localhost:9003/v1.0/sources').json()

    for item in sources_d:
        item.update({"selected": 1})

    return render_template('search_page.html', query="", form_data=sources_d)


@app.route('/search', methods=['GET'])
def get_search():
    sources_d = requests.get('http://localhost:9003/v1.0/sources').json()

    source_choice = request.args.get('sources', None)
    source_choice_int = [int(n) for n in source_choice.split()]

    # update source selection
    if source_choice_int:
        for item in sources_d:
            if item['id'] not in source_choice_int:
                item['selected'] = 0

    print("sources d")
    print(sources_d)
    # ?author=<author>&title=<title>&year=<year>&isbn=<isbn>&doi=<doi>&sources=<sources>
    # http://localhost:9090/search?author=one&title=two&year=three&isbn=1234567891&doi=doix1234567&sources=0+1+2+3+4
    author  = request.args.get('author', '')
    title  = request.args.get('title', '')
    year = request.args.get('year', '')
    doi = request.args.get('doi', '')
    isbn = request.args.get('isbn', '')

    print("--- get search init ---")
    # print(author, title, year, isbn, doi, sources)
    # q = {"author": author, "title": title, "year": year, "isbn": isbn, "doi": doi, "sources": sources}

    query = "http://localhost:9003/v1.0/simple/items?"+request.query_string.decode("utf-8")
    print("query")
    print(query)

    radovan = requests.get(query)

    try:
        print(radovan)
        return_data = radovan.json()
    except Exception as e:
        print(e)
        return_data = {"Message": "No results."}

    return render_template('results.html', return_data=return_data, form_data=sources_d, title=title, author=author, year=year, doi=doi, isbn=isbn)


@app.route('/results', methods=['GET', 'POST'])
def results():
    sources_d = requests.get('http://localhost:9003/v1.0/sources').json()

    for item in sources_d:
        item.update({"selected": 1})

    if request.method == 'POST':
        r = request.form.to_dict()

        selection = request.form.getlist('providers')
        sel_int = [int(i) for i in selection]

        for item in sources_d:
            if item['id'] not in sel_int:
                item.update( {"selected": 0})

        sources = '+'.join(selection)

        query = '?author='+r['author']+'&title='+r['title']+'&year='+r['year']+'&isbn='+r['isbn']+'&doi='+r['doi']+'&sources='+sources

        radovan = requests.get('http://localhost:9003/v1.0/simple/items'+query)

        try:
            return_data = radovan.json()
        except Exception as e:
            logging.debug("Error displaying results: ", e)
            return_data = ''

        return render_template('results.html', return_data=return_data, form_data=sources_d, title=r['title'], author=r['author'], year=r['year'], doi=r['doi'], isbn=r['isbn'])


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="9090")
