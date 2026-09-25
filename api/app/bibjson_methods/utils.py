import re

def convert_fielddata_to_list(fielddata):
    if isinstance(fielddata, list):
        return fielddata
    elif isinstance(fielddata, dict):
        return []
    elif isinstance(fielddata, str):
        if ';' in fielddata:
            return fielddata.split(';')
        else:
            return fielddata.split(',')
    return []


def flatten_dict_values(slovar):
    output = []
    for value in slovar.values():
        if isinstance(value, list):
            output.extend(value)
    return output


def convert_to_bibjson_key(slovar, alias):
    """ Return correnct bibjson term based on input variable name. """
    for key, value in slovar.items():
        if alias in value:
            return key


def gen_dict_extract(key, var):
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


def dict_path(path, my_dict, out):
    for k, v in my_dict.items():
        if isinstance(v, dict):
            dict_path(path+"['"+k+"']", v, out)
        elif isinstance(v, list):
            for blj in v:
                dict_path(path+"['"+k+"']",blj,out)
        else:
            struct = {'path': path+"['"+k+"']", 'value': v}
            out.append(struct)


def return_data_type(data_value):
    if isinstance(data_value, dict):
        return "dict"
    elif isinstance(data_value, list):
        return "list"
    elif isinstance(data_value, str):
        return "string"
    else:
        return None


def resolve_depth(settings, level):
    for s in settings:
        if s['level'] == level:
            depth = s['depth']
            return depth
    return None


# TO DO: duplicate see api request validations
def extract_dois(text):
    """Extract DOIs from the string."""
    doi_regex = re.compile(
        r"""10\.\d{4,9}/[^\s"'<>]+""",
        re.IGNORECASE
    )
    if not text:
        return []

    candidates = doi_regex.findall(text)

    # cleanup common trailing punctuation
    return [
        doi.rstrip(".,;:)") for doi in candidates
    ]


def resolve_nice_type(original_type, types):
    """ Standardizes type names based on aliases in types. """
    for i in types:
        type_name = list(i.keys())[0]
        if original_type in i[type_name]['aliases']:
            return type_name

    return ""


def extract_original_type(value):
    if isinstance(value, list):
        return value[0].lower()
    elif isinstance(value, dict):
        tmp_typ = value[next(iter(value))]
        try:
            return tmp_typ.split('/')[-1]
        except:
            return value[next(iter(value))]
    else:
        return value.lower()
