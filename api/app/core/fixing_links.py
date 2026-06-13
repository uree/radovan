import pprint

pp = pprint.PrettyPrinter(indent=4)


# FORMATTING LINKS
def url_constructor(name, type, link):
    names = ['landing_url', 'download_url', 'open_url']
    one_link = {'name': '', 'href': '', 'type': ''}
    try:
        if link.startswith('/b/?'):
            uplink = link.replace('/b/?', '')
        else:
            uplink = link
        link_dict = dict({'name': name, 'type': type, 'href': uplink})
        return link_dict
    except IndexError:
        pass


# tying links to probable function (open, download, landing) based on experience with pages
def standardize_links(source, data, keep=False):
    # keep = keep information contained in type
    standard_type = {'doab': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'monoskop': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'PDF']}, 'libgen_book': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'libgen_article': {'test': 'type', 'download_aliases': ['download_url', 'Sci-Hub'], 'landing_aliases': ['landing_url', 'Libgen.lc'], 'open_aliases': ['open_url']}, 'doaj': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'fulltext'], 'href_alias': 'url'}, 'osf': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'scielo': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'memoryoftheworld': {'test': 'format', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'core': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'View in browser']}, 'aaaaarg': {'test': 'url', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url'], 'href_alias': 'url'}, 'aaaaarg': {'test': 'url', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url'], 'href_alias': 'url'}}

    try:
        test_src = standard_type[source]
    except:
        return data

    if standard_type[source]['test'] == 'type':
        if data['type'] in standard_type[source]['download_aliases']:
            data['type'] = "download_url"
            data['name'] = "download"
        elif data['type'] in standard_type[source]['landing_aliases']:
            data['type'] = "landing_url"
        elif data['type'] in standard_type[source]['open_aliases']:
            data['type'] = "open_url"
            data['name'] = "open"
        else:
            data['type'] = "other_url"

        # not all links are hrefs
        try:
            alias = standard_type[source]['href_alias']
            data['href'] = data[alias]
            del data[alias]
        except:
            pass


    elif standard_type[source]['test'] == 'format':
        if data['format'] == 'pdf':
            data['type'] = 'open_url'
            data['name'] = 'open'
        else:
            data['type'] = 'download_url'
            data['name'] = 'download'

    elif standard_type[source]['test'] == 'url':
        try:
            if data['type'] == 'landing_url':
                data['type'] = "landing_url"
                data['name'] = "landing"
        except:
            if data['url'].endswith('pdf'):
                data['type'] = "open_url"
                data['name'] = "open"
            else:
                data['type'] = "download_url"
                data['name'] = "download"

        # not all links are hrefs
        try:
            alias = standard_type[source]['href_alias']
            data['href'] = data[alias]
            del data[alias]
        except:
            pass

    else:
        pass

    if keep == True:
        # tell them to save info in name?
        print("keep")

    return data
