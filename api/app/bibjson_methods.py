# -*- coding: utf-8 -*-
# python 3.7.2

import json
import re
import os.path
from collections import Counter
import pprint
from fixing_links import standardize_links

import logging


# SETTINGS
bibjson_aliases = {'abstract': ['abstract', 'AB'], 'address': ['address'], 'annote': ['annote', 'descr', 'desc', 'N2'], 'booktitle': ['booktitle'], 'chapter': ['chapter'], 'crossref': ['crossref'], 'edition': ['edition'], 'howpublished': ['howpublished'], 'institution': ['institution'], 'key': ['key'], 'month': ['month'], 'note': ['note'], 'number': ['number'], 'organization': ['organization'], 'pages': ['pages', 'page'], 'publisher': ['publisher', 'PB', 'publishers'], 'school': ['school'], 'series': ['series'], 'title': ['title', 'TI', 'titleInfo', 'Title'], 'type': ['type', 'TY', 'genre', 'ENTRYTYPE'], 'volume': ['volume', 'VL'], 'year': ['year', 'PY', 'Year', 'publish_date'], 'author': ['author', 'AU', 'contributors', 'name', 'z_authors', 'Authors'], 'editor': ['editor'], 'identifier': ['doi', 'identifier', 'identifierwodash', 'md5', 'issn', 'isbn', 'ID', 'SN', 'DO', 'issne', 'issnp', 'identifiers', 'journal_issns', 'ISBN-13', 'olid', 'isbn-10'], 'link': ['locator', 'url', 'href', 'L1', 'UR', 'url_for_pdf', 'url_for_landing_page', 'best_oa_location', 'links', 'link'], 'subject': ['subject', 'KW', 'subjects'], 'journal': ['journal']}

extra_aliases = {'coverurl': ['coverurl', 'img_href'], 'language': ['language', 'LA', 'languages'], 'pagesinfile': ['pagesinfile'], 'tags': ['tags'], 'filetype': ['extension'], 'source': ['source'], 'rank': ['rank'], 'place_published': ['CY'], 'issue': ['IS', 'issue'], 'startpage': ['SP'], 'lastpage': ['EP'], 'md5': ['md5'], 'landing_url': ['landing_url'], 'query': ['query']}

# careful = ['core']
#lvl2_aliases = {'core': {'name': {'affiliation': ['extra', 'affiliation']}, {'namePart':['bibjson', 'author']}},

#type_aliases = {'type': ['TY', 'genre', 'type']}

# careful_aliases = {"name": [{"path": "['namePart'][0][0]['text']", "condition": {"@type": "family"}, "in_nice_key": "name"}, {"path": "['namePart'][0][1]['#text']", "condition": {"@type": "given"}, "in_nice_key": "name"}], "originInfo": {"path": "['dateIssued']['#text']", "in_nice_key": "year"}, "relatedItem": [{"path": "['relatedItem']['part']['extent']['start']", "in_nice_key": "startpage"}, {"path": "['relatedItem']['part']['extent']['end']", "in_nice_key": "lastpage"}, {"path": "['relatedItem']['part']['detail']['number']", "in_nice_key": "issue"}, {"path": "['relatedItem']['identifier']['#text']", "in_nice_key": "identifier"}], "titleInfo": {"path": "['title']", "in_nice_key": "title"}}

fields = {'strings': ['abstract', 'address', 'annote', 'booktitle', 'chapter', 'crossref', 'edition', 'howpublished', 'institution', 'key', 'month', 'note', 'number', 'organization', 'pages', 'publisher', 'school', 'series', 'title', 'type', 'volume', 'year', 'journal', 'language'], 'list_of_dicts': ['author', 'editor', 'identifier', 'link', 'subject'], 'objects': ['']}

types = [{'article': {'required': ['author', 'title', 'journal', 'year', 'volume'], 'optional': ['number', 'pages', 'month', 'note', 'key'], 'aliases': ['article', 'jour', 'JOUR']}}, {'book': {'required': ['author', 'editor', 'title', 'publisher', 'year'], 'optional': ['volume', 'number', 'series', 'address', 'edition', 'month', 'note', 'key', 'url', 'type'], 'aliases': ['book', 'edition', 'work']}}, {'booklet': {'required': ['title'], 'optional': ['author', 'howpublished', 'address', 'month', 'year', 'note', 'key'], 'aliases': ['booklet']}}, {'conference': {'required': ['author', 'editor', 'title', 'chapter/pages', 'publisher', 'year'], 'optional': ['volume', 'number', 'series', 'type', 'address', 'edition', 'month', 'note', 'key'], 'aliases': ['conference']}}, {'inbook': {'required': ['author', 'title', 'booktitle', 'publisher', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'type', 'chapter', 'pages', 'address', 'edition', 'month', 'note', 'key'], 'aliases': ['inbook']}}, {'incollection': {'required': ['author', 'title', 'booktitle', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note', 'key'], 'aliases': ['incollection']}}, {'inproceedings': {'required': ['author', 'title', 'booktitle', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'pages', 'address', 'month', 'organization', 'publisher', 'note', 'key'], 'aliases': ['inproceedings', 'conference paper']}}, {'manual': {'required': ['title'], 'optional': ['author', 'organization', 'address', 'edition', 'month', 'year', 'note', 'key'], 'aliases': ['manual']}}, {'masterthesis': {'required': ['author', 'title', 'school', 'year'], 'optional': ['type', 'address', 'month', 'note', 'key'], 'aliases': ['masterthesis']}}, {'misc': {'required': ['none'], 'optional': ['author', 'title', 'howpublished', 'month', 'year', 'note', 'key'], 'aliases': ['misc', 'creative work', 'artwork']}}, {'phdthesis': {'required': ['author', 'title', 'school', 'year'], 'optional': ['type', 'address', 'month', 'note', 'key'], 'aliases': ['phdthesis']}}, {'proceedings': {'required': ['title', 'year'], 'optional': ['editor', 'volume', 'number', 'series', 'address', 'month', 'publisher', 'organization', 'note', 'key'], 'aliases': ['proceedings']}}, {'techreport': {'required': ['author', 'title', 'institution', 'year'], 'optional': ['type', 'number', 'address', 'month', 'note', 'key'], 'aliases': ['techreport']}}, {'unpublished': {'required': ['author', 'title', 'note'], 'optional': ['month', 'year', 'key'], 'aliases': ['unpublished']}}]

current_source = ''

resolving_nesting = [{'test': {'problem_fields': [{'field_name': 'title', 'depth_and_keys': 'title'}]}, 'aaaaarg': {'problem_fields': [{'field_name': 'language', 'depth_and_keys': 'key'}]}}]

#sources_bibjson = [{'doaj': [{'level': 'hits','depth': 'results'}, {'level': 'hit', 'depth': 'bibjson'}]}]
sources_bibjson = [{'doaj': [{'level': 'hit', 'depth': 'bibjson'}]}]

logging.basicConfig(filename='logs/bibjson_methods_log.log', level=logging.DEBUG, format='%(asctime)s:%(levelname)s:%(message)s')
pp = pprint.PrettyPrinter(indent=4)


def join_lists(slovar):
    list = []
    for key, value in slovar.items():
        if len(value)>1:
            list.append(value)
        else:
            pass
    return list

def join_lists2(slovar):
    oput = []
    for k, v in slovar.items():
        for xx in v:
            oput.append(xx)
    return oput

def dis_ambig(slovar, alias):
    for key, value in slovar.items():
        if alias in value:
            return key

def gen_dict_extract(key, var):
    all_paths = []
    if hasattr(var,'iteritems'):
        for k, v in var.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result

def get_all_keys(dict_item, key_base=''):
    all_paths = []
    if isinstance(dict_item, dict):
        for key in dict_item:
            if key_base:
                new_key = key_base + "/" + key
            else:
                new_key = key
            all_paths.extend(get_all_keys(dict_item[key], new_key))
    else:
        if key_base:
            all_paths.append(key_base)

    return all_paths

def really_get_all_keys(dict_item, key_base=''):
    all_paths = []
    if isinstance(dict_item, dict):
        for key in dict_item:
            if key_base:
                new_key = key_base + "/" + key
            else:
                new_key = key
            all_paths.extend(really_get_all_keys(dict_item[key], new_key))
    else:
        if key_base:
            all_paths.append(key_base)

    return all_paths


def dict_path(path,my_dict,out):
    for k,v in my_dict.items():
        if isinstance(v,dict):
            dict_path(path+"['"+k+"']",v,out)
        elif isinstance(v,list):
            for blj in v:
                dict_path(path+"['"+k+"']",blj,out)
        else:
            struct = {'path': path+"['"+k+"']", 'value': v}
            out.append(struct)



def parse_keys(all_paths, search_key):
    output = []

    if all_paths:
        for i in all_paths:
            op = i.split('/')
            mar = [n for n in op if op[-1] == search_key]
            if mar:
                output.append(mar)

    return output


def return_data_type(data_value):
    if isinstance(data_value, dict):
        return "dict"
    elif isinstance(data_value, list):
        return "list"
    elif isinstance(data_value, str):
        return "string"
    else:
        return None

def resolve_depth(pod, source, level):
    depth = ''
    for i in pod:
        #print(i)
        if source in i:
            for k, v in i.items():
                for s in v:
                    if s['level'] == level:
                        depth = s['depth']
    return depth

def get_it(lod, val):
    for i in lod:
        if val in i:
            return True
        else:
            return False



# GENERATING STANDARD BIBJSON DATA TYPES FROM MESSY INPUTS

## STRINGS // not really necessary
def make_string(fieldname, fielddata):
    return dict(fieldname=fielddata)



## LISTS OF DICTS
def list_of_dicts(fieldname, fielddata, original_key, source):
    logging.info("Processing list_of_dicts ...")

    output = []

    if type(fielddata) == list:
        nice_input = fielddata
    elif type(fielddata) == dict:
        pass
    else:
        if ";" in fielddata:
            try:
                nice_input = fielddata.split(';')
                #print nice_input
            except:
                pass
        else:
            try:
                nice_input = fielddata.split(',')
            except:
                pass

    if fieldname == "author":
        #print("Ordering authors ... ")
        #print(fielddata)
        if source == "oadoi":
            all = []
            if isinstance(fielddata, list):
                for i in fielddata:
                    one = {"name": "", "alternate": [""],  "firstname": "", "lastname": ""}
                    try:
                        one['firstname'] = i['given']
                        one['lastname'] = i['family']
                        one["name"] = i['given']+" "+i['family']

                        all.append(one)
                    except TypeError:
                        pass
                output = all
            else:
                pass

        else:
            try:
                for i in nice_input:
                    one =  {"name": "", "alternate": [""],  "firstname": "", "lastname": "", "type": "author"}

                    # this works for aarg let's hope it doesn't ruin anything elsewhere
                    ftype = return_data_type(i)
                    if ftype == 'dict':
                        ks = get_all_keys(i)
                        tmp = gen_dict_extract(ks[0], i)
                        lst = [el for el in tmp]
                        one['name'] = lst[0]
                        output.append(one)
                    else:
                        one['name'] = i
                        output.append(one)

            except Exception as e:
                pass


    elif fieldname == "editor":
        try:
            for i in nice_input:
                one =  {"name": "", "alternate": [""],  "firstname": "", "lastname": "", "type": "editor"}
                one['name'] = i
                output.append(one)
        except:
            pass

    elif fieldname == "identifier":
        # need a test here?
            # recognize DOI and ISBN
            # split if contains space slash or comma?
        def appendix(input_lst, keyname=original_key):
            for i in input_lst:
                one = {"id": "", "type": ""}
                one['type'] = keyname
                one['id'] = i
                output.append(one)

        def appendone(input_val, keyname=original_key):
                one = {"id": "", "type": ""}
                one['type'] = keyname
                one['id'] = input_val
                output.append(one)

        if type(fielddata) == list:
            br = ' '.join(fielddata)

            isbns = re.findall(r"\d{10,13}", br)

            dois = re.findall(r"/^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i", br)

            if len(isbns)>1:
                appendix(isbns, "isbn")
            else:
                pass

            if len(dois)>1:
                appendix(dois, "doi")
            else:
                try:
                    #specifically because of osf ...
                    dois2 = re.findall(r"10.[-._;()/:A-Z0-9]+$", br)
                    appendix(dois2, "doi")
                except:
                    pass
        elif type(fielddata) == dict:
            #print(fielddata)
            pass

        else:
            appendone(fielddata)


    elif fieldname == "link":
        one = {'name': '','type': '', 'href': ''}
        if type(fielddata)==list:

            if isinstance(fielddata[0], dict):
                for i in fielddata:
                    i2 = standardize_links(source, i)
                    output.append(i2)
            else:
                for i in fielddata:
                    try:
                        for key, value in i.items():
                            one['href'] = value
                            output.append(one)
                    except:
                        one['href'] = i
                        output.append(one)

        elif type(fielddata) == dict:
            if source =="oadoi":
                # skipping link standardization
                for k, v in fielddata.items():
                    tmp = {}
                    if k == 'url_for_pdf':
                        tmp['type'] = 'open_url'
                        tmp['href'] = v
                        tmp['name'] = 'open'
                    elif k == 'url_for_landing_page':
                        tmp['type'] = 'landing_url'
                        tmp['href'] = v
                        tmp['name'] = 'landing'
                    elif k == 'url':
                        tmp['type'] = 'open_url'
                        tmp['href'] = v
                        tmp['name'] = 'open'

                    if not tmp:
                        pass
                    else:
                        output.append(tmp)
            else:
                output.append(fielddata)
        else:
            try:
                if source == 'oapen':
                    if 'download' in fielddata:
                        one['type'] = 'download_url'
                        one['name'] = 'download'
                    else:
                        one['type'] = 'landing_url'
                        one['name'] = 'landing page'
                elif source == 'scielo':
                    one['type'] = 'open_url'
                    one['name'] = 'open'


                one['href'] = fielddata
                output.append(one)
            except:
                pass


    elif fieldname == "subject":
        for i in fielddata:
            output.append(i)

    return output

    # author =  [{"name": "", "alternate": [""],  "firstname": "", "lastname": ""}]
    #
    # editor = [{"name": "", "alternate": [""],  "firstname": "", "lastname": ""}]
    #
    # identifier = [{"id": "", "type": ""}]
    #
    # link = [{"content_type":"", "type":"", "url":""}]
    #
    # subject = [{"code": "", "scheme": "", "term": ""}]

# NESTED DICTS
def make_a_journal(journaldata):
    logging.info("Processing make_a_journal ...")

    j_fields = ['issns', 'language', 'publisher', 'journal', 'volume', 'pages', 'year', 'issue', 'month']

    j_dict = {}
    out = {'bibjson': [], 'extra': []}
    bibout = {}
    extraout = {}

    for k, v in journaldata['bibjson'][0].items():

        if k in j_fields:
            j_dict[k] = v
        else:
            bibout[k] = v


    for k, v in journaldata['extra'][0].items():
        if k in j_fields:
            j_dict[k] = v
        else:
            extraout[k] = v

    out['bibjson'].append(bibout)
    out['extra'].append(extraout)
    out['bibjson'][0]['journal'] = j_dict
    return out





def type_maker(type, data_key, data_value, source):
    logging.info("Processing type_maker ...")

    bibjson = {}
    af2 = []
    for i in types:
        if type in i:
            af = join_lists(i[type])
            af2 = af[0]+af[1]
        else:
            pass

    new_key = dis_ambig(bibjson_aliases, data_key)


    if new_key in fields['strings']:
        dv = return_data_type(data_value)

        if dv != 'string':
            for s in resolving_nesting:
                if source in s:
                    #print(s[source])
                    pf = s[source]['problem_fields']
                    for f in pf:
                        if f['field_name'] == new_key:
                            temp = data_value[f['depth_and_keys']]
                            #print(temp)
                            data_value = temp
                else:
                    pass

        bibjson[new_key] = data_value


    elif new_key in fields['list_of_dicts']:
        lod = list_of_dicts(new_key, data_value, data_key, source)
        bibjson[new_key] = lod
    elif new_key in fields['objects']:
        bject = make_a_journal(new_key, data_value, data_key)

    return bibjson

# file for testing
source ='stuff/arg_output.json'

# CONTROLLER FUNCTION
def mein_main(incoming):
    hits = {'hits': []}
    logging.info("Initiated mein_main ...")
    hit = {'bibjson': []}
    meta = {'hits_per_source': []}


    try:
        os.path.isfile(incoming)
        f = open(incoming)
        data = json.load(f)
        data = data['entries']
    except TypeError:
        data = incoming['entries']

    # this is where i could count the hits?
    for i in data:
        new_hits = []

        try:
            source = list(i.keys())[0]
        except Exception as e:
            return "Error"
        global current_source
        current_source = source

        hit_count = {'source': source, 'count': len(i[source]['hits'])}
        meta['hits_per_source'].append(hit_count)

        try:
            for x in i[source]['hits']:
                new_hits.append(x)
        except TypeError:
            pass


        # rename all the compatible fields?
        ea = join_lists2(extra_aliases)
        bt = join_lists2(bibjson_aliases)

        #print(json.dumps(i, sort_keys=True, indent=4))

        for i in new_hits:
            hit = {"bibjson": [], "extra": []}
            bibjson_output = {}
            extra_output = {}
            extra_fields = {}
            bibjson_fields = {}
            original_type = ''
            nice_type = ''
            past_keys = []

            cs = {"source": current_source}


            # for results which come in the form of bibjson (doaj only currently)
            if get_it(sources_bibjson, current_source):
                #count = 0
                cleaner = resolve_depth(sources_bibjson, current_source, 'hit')

                extra = {}
                extra['source'] = current_source
                extra['rank'] = i[cleaner]['rank']
                extra['query'] = i[cleaner]['query']

                #dirty hack for doaj, only thing ending here
                hit['extra'].append(extra)
                del i[cleaner]['rank']

                hit_tmp = [standardize_links(current_source, n) for n in i[cleaner]['link']]
                i[cleaner]['link'] = hit_tmp

                hit['bibjson'].append(i[cleaner])

                hits['hits'].append(hit)
                #count+=1
            else:
                if isinstance(i, dict):
                    for key, value in i.items():
                        mua = {}

                        listo = bibjson_aliases['type']

                        # extracts original type value
                        if key in listo:
                            if isinstance(value, (list)):
                                original_type = value[0].lower()
                            elif isinstance(value, dict):
                                tmp_typ = value[next(iter(value))]
                                #print(tmp_typ)
                                try:
                                    original_type = tmp_typ.split('/')[-1]
                                    #print(original_type)
                                except:
                                    original_type = value[next(iter(value))]
                            else:
                                original_type = value.lower()


                        # translates keys to standard values
                        if key in ea:
                            try:
                                extra_fields[dis_ambig(extra_aliases, key)] = value
                            except Exception as e:
                                pass
                        elif key in bt:
                            try:
                                bibjson_fields[key] = value
                            except Exception as e:
                                pass
                        else:
                            pass
                else:
                    pass


                # standardizes type names based on aliases in types (top)
                # print("Resolving item type ...")
                for i in types:
                    type_name = list(i.keys())[0]

                    if original_type in i[type_name]['aliases']:
                        #print("Original type in aliases.")
                        nice_type = type_name
                    else:
                        #print("Original type NOT in aliases.")
                        pass

                for key, value in bibjson_fields.items():

                    # IF NICE TYPE IS MISSING ASSIGN misc
                    if nice_type == '':
                        nice_type = 'misc'


                    # USES CLEANED UP TYPE VLAUE IF TYPE FIELD IS BEING PROCESSED
                    # hack in the case of scielo ... optimize when time
                    if key == "type" or key == "TY":
                        value = nice_type

                    bibjson_one = type_maker(nice_type, key, value, source)



                    if bool(bibjson_one) == True:
                        for k, v in bibjson_one.items():
                            #print k, v
                            #checks if value already exists in bibjson output ... if so it needs to be appended to existing bibjson differently
                            if k in past_keys:
                                if type(v)==list:
                                    try:
                                        for i in v:
                                            bibjson_output[k].append(i)
                                    except:
                                        pass
                                else:
                                    try:
                                        bibjson_output[k].append(v)
                                    except:
                                        pass
                            else:
                                try:
                                    bibjson_output[k] = v
                                except:
                                    pass

                    if list(bibjson_one.keys())[0] not in past_keys:
                        past_keys.append(list(bibjson_one.keys())[0])

                for key, data_value in extra_fields.items():
                    # checks if data is weirdly nested
                    for s in resolving_nesting:
                        if source in s:
                            pf = s[source]['problem_fields']
                            for f in pf:
                                if f['field_name'] == key:
                                    # this is not sustainable
                                    if return_data_type(data_value) == "list":
                                        data_value = data_value[0]

                                    temp = data_value[f['depth_and_keys']]
                                    data_value = temp
                        else:
                            pass

                    extra_output[key] = data_value

                extra_output['source'] = current_source

                hit['bibjson'].append(bibjson_output)
                hit['extra'].append(extra_output)


                # CORRECTION IF IT'S A JOURNAL
                # this is where the <built in method> issue arises. sometimes?
                try:
                    if bibjson_output['type'] == 'article':
                        hit = make_a_journal(hit)
                except KeyError:
                    pass


                #print(json.dumps(hit, sort_keys=True, indent=4))

                hits['hits'].append(hit)

    hits['meta'] = meta
    return hits
