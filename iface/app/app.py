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
global sources_d
r = requests.get('http://localhost:9003/v1.0/sources').json()

for item in r:
    item.update( {"selected": 1})

sources_d = r

@app.route('/')
def search():
    return render_template('search_page.html', query="", form_data=sources_d)


@app.route('/results?author=<author>', methods=['GET', 'POST'])
def results():
    if request.method == 'POST':
        r = request.form.to_dict()

        selection = request.form.getlist('providers')
        sel_int = [int(i) for i in selection]

        for item in sources_d:
            if item['id'] not in sel_int:
                item.update( {"selected": 0})

        sources = '+'.join(selection)

        query = '?author='+r['author']+'&title='+r['title']+'&year='+r['year']+'&isbn='+r['isbn']+'&doi='+r['doi']+'&sources='+sources
        print(query)

        r = requests.get('http://localhost:9003/v1.0/simple/items'+query)

        try:
            return_data = r.json()
        except Exception as e:
            logging.debug("Error displaying results: ", e)
            return_data = ''

        return render_template('results.html', return_data=return_data, form_data=sources_d)


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="9090")
