def url_constructor(name, type, link):
    try:
        if link.startswith('/b/?'):
            uplink = link.replace('/b/?', '')
        else:
            uplink = link
        link_dict = {"name": name, "type": type, "href": uplink}
        return link_dict
    except IndexError:
        pass

# TO DO: this has a bad name and is used in bibjson_methods ... so it should live there
# tying links to probable function (open, download, landing) based on experience with pages
def standardize_links(source, data, keep=False):
    # keep = keep information contained in type
    standard_type = {'doab': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'monoskop': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'PDF']}, 'libgen': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'doaj': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url', 'fulltext'], 'href_alias': 'url'}, 'osf': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'scielo': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'memoryoftheworld': {'test': 'format', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url']}, 'mlacore': {'test': 'type', 'download_aliases': ['download_url'], 'landing_aliases': ['self_html'], 'open_aliases': ['open_url', 'View in browser']}, 'aaaaarg': {'test': 'url', 'download_aliases': ['download_url'], 'landing_aliases': ['landing_url'], 'open_aliases': ['open_url'], 'href_alias': 'url'}}

    try:
        test_src = standard_type[source]
    except:
        return data

    if standard_type[source]['test'] == 'type':
        if data['type'] in standard_type[source]['download_aliases']:
            data['type'] = "direct_download"
            data['name'] = "direct download"
        elif data['type'] in standard_type[source]['landing_aliases']:
            data['type'] = "landing_page"
            data['name'] = "landing page"
        elif data['type'] in standard_type[source]['open_aliases']:
            data['type'] = "full_text"
            data['name'] = "full text"
        else:
            data['type'] = "unknown"
            data['name'] = "unknown"

        # not all links are hrefs
        try:
            alias = standard_type[source]['href_alias']
            data['href'] = data[alias]
            del data[alias]
        except:
            pass


    elif standard_type[source]['test'] == 'format':
        if data['format'] == 'pdf':
            data['type'] = 'full_text'
            data['name'] = 'full text'
        else:
            data['type'] = 'direct_download'
            data['name'] = 'direct download'

    elif standard_type[source]['test'] == 'url':
        try:
            if data['type'] == 'landing_url':
                data['type'] = "landing_page"
                data['name'] = "landing page"
        except:
            if data['url'].endswith('pdf'):
                data['type'] = "full_text"
                data['name'] = "full text"
            else:
                data['type'] = "direct_download"
                data['name'] = "direct download"

        # not all links are hrefs
        try:
            alias = standard_type[source]['href_alias']
            data['href'] = data[alias]
            del data[alias]
        except:
            pass

    else:
        pass

    return data
