# -*- coding: utf-8 -*-
# python 3.6.9

def validate_parameters(rargs):
    """
    Validates query parameters takes request.args (ImmutableDict) as input:
        - is there at least one parameter beside sources present,
        - is isbn valid,
        - is doi valid.
    """

    # is there at least one parameter present which is not sources?
    if not any(len(v) != 0 and k !="sources" for k, v in rargs.items()):
        return {"valid_query": False, "message": "No valid parameters provided. The query must contain at least one of the following: author, title, year, doi, isbn.", "sample_query": "/radovan/api/search/single?author=miller&title=&year=2010&isbn=&doi=&sources=2+3"}

    # is isbn in the right format
    isbn = rargs.get('isbn')
    if isbn != None:
        if len(isbn) != 0:
            isbn_clean = isbn.strip().replace('-','')

            if len(isbn_clean) not in [10, 13]:
                return {"valid_query": False, "message": "Invalid ISBN. Accepts ISBN10 or ISBN13 with or without dashes."}

    # is doi in the right format
    # https://support.datacite.org/docs/doi-basics

    doi = rargs.get('doi')
    if doi != None:
        if len(doi) != 0:
            if not doi.startswith('10.'):
                return {"valid_query": False, "message": "Misformatted DOI. Should start with 10.", "sample_query": "10.5061/DRYAD.0SN63/7"}

    # all ok
    return {"valid_query": True}
