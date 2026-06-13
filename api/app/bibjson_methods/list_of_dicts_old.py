def list_of_dicts(fieldname, fielddata, original_key, source):
    """ Convert a list of dictionaries into valid bibjson and extra fields. """

    output = []

    if fielddata != None:
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
        if source == "oadoi":
            all = []
            if isinstance(fielddata, list):
                for i in fielddata:
                    one = {"name": "", "alternate": [""],  "firstname": "", "lastname": ""}
                    try:
                        one['firstname'] = i['given']
                        one['lastname'] = i['family']
                        one['name'] = i['given']+" "+i['family']

                        all.append(one)
                    except TypeError:
                        pass
                output = all
            else:
                pass
        elif source == "doab" or source == "oapen":
                one = {"name": "", "alternate": [""],  "firstname": "", "lastname": ""}

                try:
                    ph = fielddata.split(', ')
                except Exception as e:
                    one['name'] = fielddata
                    output.append(one)
                    pass

                try:
                    one['firstname'] = ph[1]
                    one['lastname'] = ph[0]
                    one['name'] = ph[1]+' '+ph[0]
                    output.append(one)
                except:
                    one['name'] = fielddata
                    output.append(one)
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

        logger.debug(fielddata)
        logger.debug(type(fielddata))

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
            pass

        else:
            if fielddata.startswith('10.') or 'doi' in fielddata:
                appendone(fielddata, 'doi')
            elif fielddata.startswith('978'):
                appendone(fielddata, 'isbn')
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
            if source == 'scielo':
                try:
                    one['type'] = 'open_url'
                    one['name'] = 'open'
                    one['href'] = fielddata
                    output.append(one)
                except:
                    pass
            elif source == 'doab' or source == 'oapen':
                if fielddata.endswith('.pdf') or fielddata.endswith('.epub'):
                    one['type'] = 'download_url'
                    one['name'] = 'download'
                else:
                    one['type'] = 'landing_url'
                    one['name'] = 'landing page'

                one['href'] = fielddata
                output.append(one)


    elif fieldname == "subject":
        for i in fielddata:
            output.append(i)

    return output
