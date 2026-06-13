def mein_main(data):
    hits = {'hits': []}
    hit = {'bibjson': []}
    meta = {'hits_per_source': []}

    if "entries" not in data:
        return hits

    # this is where i could count the hits?
    for i in data["entries"]:
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
        extra_aliases_flat = flatten_dict_values(extra_aliases)
        bibjson_aliases_flat = flatten_dict_values(bibjson_aliases)

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
                cleaner = resolve_depth(sources_bibjson, current_source, 'hit')

                extra = {}
                extra['source'] = current_source
                extra['rank'] = i[cleaner]['rank']
                extra['query'] = i[cleaner]['query']

                # dirty hack for doaj, only thing ending here
                hit['extra'].append(extra)
                del i[cleaner]['rank']

                hit_tmp = [standardize_links(current_source, n) for n in i[cleaner]['link']]
                i[cleaner]['link'] = hit_tmp

                hit['bibjson'].append(i[cleaner])

                hits['hits'].append(hit)
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

                        # translate keys to standard values
                        if key in extra_aliases_flat:
                            try:
                                extra_fields[convert_to_bibjson_key(extra_aliases, key)] = value
                            except Exception as e:
                                pass
                        elif key in bibjson_aliases_flat:
                            try:
                                bibjson_fields[key] = value
                            except Exception as e:
                                pass
                        else:
                            pass
                else:
                    pass

                # standardizes type names based on aliases in types (top)
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
                    logger.debug(nice_type)
                    logger.debug(key)
                    logger.debug(value)
                    logger.debug(source)
                    bibjson_one = convert_data_to_bibjson(nice_type, key, value, source)

                    if bool(bibjson_one) == True:
                        for k, v in bibjson_one.items():
                            # print k, v
                            # checks if value already exists in bibjson output ... if so it needs to be appended to existing bibjson differently
                            if k in past_keys:
                                if type(v) == list:
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
                    logger.debug(bibjson_one)
                    if bibjson_one:
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
                                    if isinstance(data_value, list):
                                        data_value = data_value[0]

                                    temp = data_value[f['depth_and_keys']]
                                    data_value = temp
                        else:
                            pass

                    extra_output[key] = data_value

                extra_output['source'] = current_source

                hit['bibjson'].append(bibjson_output)
                hit['extra'].append(extra_output)

                # correction if it's a journal article
                try:
                    if bibjson_output['type'] == 'article':
                        bibout, extraout, jdict = process_nested_dict(hit)
                        hit['bibjson'].append(bibout)
                        hit['extra'].append(extraout)
                        hit['bibjson'][0]['journal'] = jdict
                except KeyError:
                    pass

                hits['hits'].append(hit)

    hits['meta'] = meta
    return hits
