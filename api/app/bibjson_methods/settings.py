# SETTINGS
bibjson_aliases = {
    "abstract": [
        "abstract",
        "AB",
        "dc.description.abstract",
        "description"
    ],
    "address": [
        "address"
    ],
    "annote": [
        "annote",
        "descr",
        "desc",
        "N2"
    ],
    "booktitle": [
        "booktitle"
    ],
    "chapter": [
        "chapter"
    ],
    "crossref": [
        "crossref"
    ],
    "edition": [
        "edition"
    ],
    "howpublished": [
        "howpublished"
    ],
    "institution": [
        "institution"
    ],
    "key": [
        "key"
    ],
    "month": [
        "month"
    ],
    "note": [
        "note"
    ],
    "number": [
        "number"
    ],
    "organization": [
        "organization"
    ],
    "pages": [
        "pages",
        "page"
    ],
    "publisher": [
        "publisher",
        "PB",
        "publishers",
        "publisher.name"
    ],
    "school": [
        "school"
    ],
    "series": [
        "series"
    ],
    "title": [
        "title",
        "TI",
        "titleInfo",
        "Title",
        "dc.title"
    ],
    "type": [
        "type",
        "TY",
        "genre",
        "ENTRYTYPE",
        "dc.type"
    ],
    "volume": [
        "volume",
        "VL"
    ],
    "year": [
        "year",
        "PY",
        "Year",
        "publish_date",
        "dc.date.issued"
    ],
    "author": [
        "author",
        "AU",
        "contributors",
        "name",
        "z_authors",
        "Authors",
        "dc.contributor.author",
        "creators",
        "raw_author_name",
    ],
    "editor": [
        "editor"
    ],
    "identifier": [
        "doi",
        "identifier",
        "identifierwodash",
        "md5",
        "issn",
        "isbn",
        "ID",
        "SN",
        "DO",
        "issne",
        "issnp",
        "identifiers",
        "journal_issns",
        "ISBN-13",
        "olid",
        "isbn-10",
        "oapen.identifier.doi",
        "oapen.identifier.isbn"
    ],
    "link": [
        "locator",
        "url",
        "href",
        "L1",
        "UR",
        "url_for_pdf",
        "url_for_landing_page",
        "best_oa_location",
        "links",
        "link",
        "standard_oapen_url"
    ],
    "subject": [
        "subject",
        "KW",
        "subjects",
        "dc.subject.other"
    ],
    "journal": [
        "journal"
    ]
}

extra_aliases = {
    "coverurl": [
        "coverurl",
        "img_href",
        "cover_url"
    ],
    "language": [
        "language",
        "LA",
        "languages",
        "dc.language"
    ],
    "pagesinfile": [
        "pagesinfile"
    ],
    "tags": [
        "tags"
    ],
    "filetype": [
        "extension"
    ],
    "source": [
        "source"
    ],
    "rank": [
        "rank"
    ],
    "place_published": [
        "CY"
    ],
    "issue": [
        "IS",
        "issue"
    ],
    "startpage": [
        "SP"
    ],
    "lastpage": [
        "EP"
    ],
    "md5": [
        "md5"
    ],
    "landing_url": [
        "landing_url"
    ],
    "download_url": [
        "download_url"
    ],
    "query": [
        "query"
    ]
}

fields = {
    "strings": [
        "abstract",
        "address",
        "annote",
        "booktitle",
        "chapter",
        "crossref",
        "edition",
        "howpublished",
        "institution",
        "key",
        "month",
        "note",
        "number",
        "organization",
        "pages",
        "publisher",
        "school",
        "series",
        "title",
        "type",
        "volume",
        "year",
        "journal",
        "language"
    ],
    "list_of_dicts": [
        "author",
        "editor",
        "identifier",
        "link",
        "subject"
    ],
    "objects": [
        ""
    ]
}

types = [
    {
        "article": {
            "required": [
                "author",
                "title",
                "journal",
                "year",
                "volume"
            ],
            "optional": [
                "number",
                "pages",
                "month",
                "note",
                "key"
            ],
            "aliases": [
                "article",
                "jour",
                "JOUR"
            ]
        }
    },
    {
        "book": {
            "required": [
                "author",
                "editor",
                "title",
                "publisher",
                "year"
            ],
            "optional": [
                "volume",
                "number",
                "series",
                "address",
                "edition",
                "month",
                "note",
                "key",
                "url",
                "type"
            ],
            "aliases": [
                "book",
                "edition",
                "work"
            ]
        }
    },
    {
        "booklet": {
            "required": [
                "title"
            ],
            "optional": [
                "author",
                "howpublished",
                "address",
                "month",
                "year",
                "note",
                "key"
            ],
            "aliases": [
                "booklet"
            ]
        }
    },
    {
        "conference": {
            "required": [
                "author",
                "editor",
                "title",
                "chapter/pages",
                "publisher",
                "year"
            ],
            "optional": [
                "volume",
                "number",
                "series",
                "type",
                "address",
                "edition",
                "month",
                "note",
                "key"
            ],
            "aliases": [
                "conference"
            ]
        }
    },
    {
        "inbook": {
            "required": [
                "author",
                "title",
                "booktitle",
                "publisher",
                "year"
            ],
            "optional": [
                "editor",
                "volume",
                "number",
                "series",
                "type",
                "chapter",
                "pages",
                "address",
                "edition",
                "month",
                "note",
                "key"
            ],
            "aliases": [
                "inbook"
            ]
        }
    },
    {
        "incollection": {
            "required": [
                "author",
                "title",
                "booktitle",
                "year"
            ],
            "optional": [
                "editor",
                "volume",
                "number",
                "series",
                "pages",
                "address",
                "month",
                "organization",
                "publisher",
                "note",
                "key"
            ],
            "aliases": [
                "incollection"
            ]
        }
    },
    {
        "inproceedings": {
            "required": [
                "author",
                "title",
                "booktitle",
                "year"
            ],
            "optional": [
                "editor",
                "volume",
                "number",
                "series",
                "pages",
                "address",
                "month",
                "organization",
                "publisher",
                "note",
                "key"
            ],
            "aliases": [
                "inproceedings",
                "conference paper"
            ]
        }
    },
    {
        "manual": {
            "required": [
                "title"
            ],
            "optional": [
                "author",
                "organization",
                "address",
                "edition",
                "month",
                "year",
                "note",
                "key"
            ],
            "aliases": [
                "manual"
            ]
        }
    },
    {
        "masterthesis": {
            "required": [
                "author",
                "title",
                "school",
                "year"
            ],
            "optional": [
                "type",
                "address",
                "month",
                "note",
                "key"
            ],
            "aliases": [
                "masterthesis"
            ]
        }
    },
    {
        "misc": {
            "required": [
                "none"
            ],
            "optional": [
                "author",
                "title",
                "howpublished",
                "month",
                "year",
                "note",
                "key"
            ],
            "aliases": [
                "misc",
                "creative work",
                "artwork"
            ]
        }
    },
    {
        "phdthesis": {
            "required": [
                "author",
                "title",
                "school",
                "year"
            ],
            "optional": [
                "type",
                "address",
                "month",
                "note",
                "key"
            ],
            "aliases": [
                "phdthesis"
            ]
        }
    },
    {
        "proceedings": {
            "required": [
                "title",
                "year"
            ],
            "optional": [
                "editor",
                "volume",
                "number",
                "series",
                "address",
                "month",
                "publisher",
                "organization",
                "note",
                "key"
            ],
            "aliases": [
                "proceedings"
            ]
        }
    },
    {
        "techreport": {
            "required": [
                "author",
                "title",
                "institution",
                "year"
            ],
            "optional": [
                "type",
                "number",
                "address",
                "month",
                "note",
                "key"
            ],
            "aliases": [
                "techreport"
            ]
        }
    },
    {
        "unpublished": {
            "required": [
                "author",
                "title",
                "note"
            ],
            "optional": [
                "month",
                "year",
                "key"
            ],
            "aliases": [
                "unpublished"
            ]
        }
    }
]

resolving_nesting = [
    {
        "test": {
            "problem_fields": [
                {
                    "field_name": "title",
                    "depth_and_keys": "title"
                }
            ]
        },
        "aaaaarg": {
            "problem_fields": [
                {
                    "field_name": "language",
                    "depth_and_keys": "key"
                }
            ]
        }
    }
]

sources_bibjson = {
    "doaj": [
        {
            "level": "hit",
            "depth": "bibjson"
        }
    ]
}
