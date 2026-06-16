import logging
import pprint

from app.core.fixing_links import standardize_links
from .process_datatypes import convert_data_to_bibjson, process_nested_dict
from .settings import bibjson_aliases, extra_aliases, types, sources_bibjson
from .utils import flatten_dict_values, convert_to_bibjson_key, resolve_depth, resolve_nice_type, extract_original_type


logger = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=4)

# TO DO: this module should create BibRecords, which can be translated into any format (implement that), but they need to be able to carry multiple urls


# TO DO: move this into the BibRecord model
def process_hit(
    hit_data,
    source,
    extra_aliases_flat,
    bibjson_aliases_flat,
    types
):
    hit = {"bibjson": [], "extra": []}
    bibjson_output = {}
    extra_output = {}
    extra_fields = {}
    bibjson_fields = {}
    original_type = ""
    nice_type = ""
    past_keys = []

    # if source returns bibjson make use it's clean and return
    if source in sources_bibjson:
        cleaner = resolve_depth(sources_bibjson[source], "hit")
        logger.debug(cleaner)
        extra = {
            'source': source,
        }
        hit['extra'].append(extra)

        hit_data[cleaner]['link'] = [standardize_links(source, link) for link in hit_data[cleaner]['link']]  # noqa:501
        hit['bibjson'].append(hit_data[cleaner])

        return hit

    # split keys into valid bibjson and extra fields
    if isinstance(hit_data, dict):
        for key, value in hit_data.items():
            listo = bibjson_aliases['type']
            if key in listo:
                original_type = extract_original_type(value)

            if key in extra_aliases_flat:
                extra_fields[convert_to_bibjson_key(extra_aliases, key)] = value
            elif key in bibjson_aliases_flat:
                bibjson_fields[key] = value

    nice_type = resolve_nice_type(original_type, types)

    # clean up/convert bibjson and append extra values/keys
    for key, value in bibjson_fields.items():
        # hacky fixes catching outliers
        if not nice_type:
            nice_type = 'misc'
        if key in ["type", "TY"]:
            value = nice_type
        bibjson_one = convert_data_to_bibjson(nice_type, key, value, source)
        logger.debug(bibjson_output)
        if bibjson_one:
            for k, v in bibjson_one.items():
                if k in past_keys:
                    if isinstance(v, list):
                        bibjson_output[k].extend(v)
                    # else:
                    #     try:
                    #         bibjson_output[k].append(v)
                    #     except Exception as e:
                    #         logger.debug(f"Error adding data to bibjson Key <{k}> Val <{v}> Error {e}")
                else:
                    bibjson_output[k] = v
                if k not in past_keys:
                    past_keys.append(k)

    for key, data_value in extra_fields.items():
        extra_output[key] = data_value

    extra_output['source'] = source
    hit['bibjson'].append(bibjson_output)
    hit['extra'].append(extra_output)

    try:
        if bibjson_output["type"] == "article":
            bibout, extraout, jdict = process_nested_dict(hit)
            hit["bibjson"].append(bibout)
            hit["extra"].append(extraout)
            hit["bibjson"][0]["journal"] = jdict
    except KeyError:
        pass

    return hit


# possible refactor of the above
# def process_hit(...):
#     if is_native_bibjson_source(...):
#         return process_native_bibjson(...)

#     bibjson_fields, extra_fields = extract_fields(...)
#     bibjson_output = convert_bibjson(...)
#     extra_output = build_extra(...)

#     hit = {
#         "bibjson": [bibjson_output],
#         "extra": [extra_output],
#     }

#     process_journal(hit)

#     return hit



def mein_main(data):
    hits = {'hits': [], 'meta': {'hits_per_source': []}}  # move this logic to API

    if "entries" not in data:
        return hits

    # TO DO: move this loop inside the provider model
    # this is a for each provider loop
    for entry in data["entries"]:
        new_hits = []
        try:
            source = list(entry.keys())[0]
        except Exception as e:
            logger.error(f"Error getting source info: {e}")

        hit_count = {'source': source, 'count': len(entry[source]['hits'])}
        hits['meta']['hits_per_source'].append(hit_count)

        # some sort of cleanup
        try:
            new_hits = entry[source]["hits"]
        except TypeError:
            pass

        extra_aliases_flat = flatten_dict_values(extra_aliases)
        bibjson_aliases_flat = flatten_dict_values(bibjson_aliases)

        # this is a for each hit in provider loop
        for hit_data in new_hits:
            hit = process_hit(
                hit_data,
                source,
                extra_aliases_flat,
                bibjson_aliases_flat,
                types
            )
            hits['hits'].append(hit)

    return hits
