# -*- coding: utf-8 -*-
# python 3.6.9

import requests
import json
from flask import Flask, request, jsonify, make_response, render_template
import collections
import pprint
import logging
from config import Config


app = Flask(__name__)
app.config['RESTFUL_JSON'] = { 'ensure_ascii': False }
app.config.from_object(Config)
api_base = app.config['API_CONTAINER_NAME']

logging.basicConfig(filename='logs/radovan_iface_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
pp = pprint.PrettyPrinter(indent=4)


@app.route('/')
def search():
    sources_d = requests.get(api_base+':9003/v1.0/sources').json()

    for item in sources_d:
        item.update({"selected": 1})

    return render_template('search_page.html', query="", form_data=sources_d)


@app.route('/search', methods=['GET'])
def get_search():
    sources_d = requests.get(api_base+':9003/sources').json()

    rargs = request.args.to_dict(flat=False)
    print(rargs)

    source_choice_int = [int(n) for n in rargs['sources']]

    # update source selection
    if source_choice_int:
        for item in sources_d:
            if item['id'] not in source_choice_int:
                item['selected'] = 0


    author  = request.args.get('author', '')
    title  = request.args.get('title', '')
    year = request.args.get('year', '')
    doi = request.args.get('doi', '')
    isbn = request.args.get('isbn', '')

    query = api_base+":9003/search/single?"+request.query_string.decode("utf-8")

    radovan = requests.get(query)

    try:
        return_data = radovan.json()
    except Exception as e:
        return_data = {"Message": "No results."}

    return render_template('results.html', return_data=return_data, form_data=sources_d, title=title, author=author, year=year, doi=doi, isbn=isbn)


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="9090")
