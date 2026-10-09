import logging
import re
import isbnlib 

from app.core.fixing_links import standardize_links
from .settings import bibjson_aliases, fields
from .utils import (
    convert_fielddata_to_list,
    return_data_type,
    get_all_keys,
    gen_dict_extract,
    extract_dois,
    convert_to_bibjson_key
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


def process_authors(fielddata, source):
    output = []
    if source == "oadoi":
        if isinstance(fielddata, list):
            for item in fielddata:
                author = {"name": "", "alternate": [""], "firstname": "", "lastname": ""}
                try:
                    author['name'] = f"{item['raw_author_name']}"
                    output.append(author)
                except (TypeError, KeyError):
                    pass
    elif source in ["doab", "oapen"]:
        author = {"name": "", "alternate": [""], "firstname": "", "lastname": ""}
        try:
            parts = fielddata.split(', ')
            author['firstname'] = parts[1]
            author['lastname'] = parts[0]
            author['name'] = f"{parts[1]} {parts[0]}"
            output.append(author)
        except (IndexError, AttributeError):
            author['name'] = fielddata
            output.append(author)
    elif source == "mlacore":  # hacky hack but this all needs to be refactored anyway
        logger.debug(fielddata)
        # for item in fielddata
        for item in fielddata:
            output.append(item)
    else:
        for item in convert_fielddata_to_list(fielddata):
            author = {"name": "", "alternate": [""], "firstname": "", "lastname": "", "type": "author"}
            ftype = return_data_type(item)
            if ftype == 'dict':
                keys = get_all_keys(item)
                tmp = gen_dict_extract(keys[0], item)
                author['name'] = tmp[0]
            else:
                author['name'] = item
            output.append(author)
    return output


def process_editors(fielddata):
    output = []
    for item in convert_fielddata_to_list(fielddata):
        editor = {"name": "", "alternate": [""], "firstname": "", "lastname": "", "type": "editor"}
        editor['name'] = item
        output.append(editor)
    return output


def process_identifiers(fielddata, original_key):
    output = []

    def _append_identifier(input_val, keyname, output):
        if isinstance(input_val, list):
            for item in input_val:
                identifier = {"id": item, "type": keyname}
                output.append(identifier)
        else:
            identifier = {"id": input_val, "type": keyname}
            output.append(identifier)

    fielddata_str = ' '.join(fielddata) if isinstance(fielddata, list) else fielddata   # noqa:501

    isbns = isbnlib.get_canonical_isbn(fielddata)
    dois = extract_dois(fielddata)

    _append_identifier(isbns, "isbn", output)
    _append_identifier(dois, "doi", output)

    return output


def process_links(fielddata, source):
    output = []
    if isinstance(fielddata, list):
        if isinstance(fielddata[0], dict):
            for item in fielddata:
                standardized_link = standardize_links(source, item)
                output.append(standardized_link)
        else:
            for item in fielddata:
                link = {'name': 'unknown', 'type': 'unknown', 'href': ''}
                try:
                    for key, value in item.items():
                        link['href'] = value
                        output.append(link)
                except AttributeError:
                    link['href'] = item
                    output.append(link)
    elif isinstance(fielddata, dict):
        if source == "oadoi":
            for k, v in fielddata.items():
                tmp = {}
                if k == 'url_for_pdf':
                    tmp['type'] = 'full_text'
                    tmp['href'] = v
                    tmp['name'] = 'full text'
                elif k == 'url_for_landing_page':
                    tmp['type'] = 'landing_page'
                    tmp['href'] = v
                    tmp['name'] = 'landing page'
                elif k == 'url':
                    tmp['type'] = 'full_text'
                    tmp['href'] = v
                    tmp['name'] = 'full text'
                if tmp:
                    output.append(tmp)
        else:
            output.append(fielddata)
    else:  # if it's not list or dict then it is a string (most likely)
        link = {'name': 'unknown', 'type': 'unknown', 'href': ''}
        if source == 'scielo':
            link['type'] = 'landing_page'
            link['name'] = 'landing page'
            link['href'] = fielddata
            output.append(link)
        elif source in ['doab', 'oapen']:
            if fielddata.endswith(('.pdf', '.epub')):
                link['type'] = 'direct_download'
                link['name'] = 'direct download'
            else:
                link['type'] = 'landing_page'
                link['name'] = 'landing page'
            link['href'] = fielddata
            output.append(link)
        else:
            link = {
                "name": "unknown",
                "type": "unknown",
                "href": fielddata,
            }
            output.append(link)
    return output


def process_list_of_dicts(fieldname, fielddata, original_key, source):
    """ Convert a list of dictionaries into valid bibjson and extra fields. """
    output = []

    if fielddata is None:
        return output

    if fieldname == "author":
        output = process_authors(fielddata, source)
    elif fieldname == "editor":
        output = process_editors(fielddata)
    elif fieldname == "identifier":
        output = process_identifiers(fielddata, original_key)
    elif fieldname == "link":
        output = process_links(fielddata, source)
    elif fieldname == "subject":
        output = fielddata if isinstance(fielddata, list) else [fielddata]

    return output


def process_nested_dict(journaldata):
    """ Convert nested dictionary into valid bibjson and extra fields. """

    j_fields = ['issns', 'language', 'publisher', 'journal', 'volume', 'pages', 'year', 'issue', 'month']  # noqa: 501

    j_dict = {}
    bibout = {}
    extraout = {}

    for k, v in journaldata["bibjson"][0].items():
        if k in j_fields:
            j_dict[k] = v
        else:
            bibout[k] = v

    for k, v in journaldata["extra"][0].items():
        if k in j_fields:
            j_dict[k] = v
        else:
            extraout[k] = v

    return bibout, extraout, j_dict


def convert_data_to_bibjson(type, data_key, data_value, source):
    """ Convert different data types to valid bibjson. """
    bibjson = {}
    new_key = convert_to_bibjson_key(bibjson_aliases, data_key)

    if not data_value:
        return bibjson

    logger.debug("Calling list of dicts {}".format(new_key))
    logger.debug("Data value {}".format(data_value))
    logger.debug("Data key {}".format(data_key))
    logger.debug("Source {}".format(source))

    # there is also code to porcess objects in process_datatypes
    if new_key in fields["strings"]:
        try:
            bibjson[new_key] = data_value
        except Exception as e:
            logger.debug(f"Failed to convert string to bibjson {e}")
    elif new_key in fields["list_of_dicts"]:
        try:
            bibjson[new_key] = process_list_of_dicts(new_key, data_value, data_key, source)
        except Exception as e:
            logger.debug(f"Failed to convert list of dicts to bibjson {e}")
    else:
        pass

    return bibjson
