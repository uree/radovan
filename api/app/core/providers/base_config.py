from dataclasses import dataclass


@dataclass
class ProviderConfig():
    id: int
    code_name: str
    full_name: str
    url: str
    query_url: str
    books: bool = True
    articles: bool = False
    selected: bool = True
    enabled: bool = True


provider_dict = [
    {
        "full_name": "Directory of Open Access Books",
        "url": "https://www.doabooks.org/",
        "code_name": "doab",
        "id": 0,
        "books": 1,
        "articles": 0,
        "query_url": "https://directory.doabooks.org/rest/search?query=",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "OAPEN",
        "url": "http://www.oapen.org/home",
        "code_name": "oapen",
        "id": 1,
        "books": 1,
        "articles": 0,
        "query_url": "https://library.oapen.org/rest/search?query=",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "Monoskop",
        "url": "https://monoskop.org/Monoskop",
        "code_name": "monoskop",
        "id": 2,
        "books": 1,
        "articles": 1,
        "query_url": "https://monoskop.org/log/?cat=17&s=",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "Library Genesis",
        "url": "https://libgen.vg",
        "code_name": "libgen_book",
        "id": 3,
        "books": 1,
        "articles": 0,
        "query_url": "https://libgen.vg/index.php",
        "selected": 1,
        "enabled": 1,
    },
    {
        "full_name": "Library Genesis Scimag",
        "url": "https://libgen.is/scimag/index.php",
        "code_name": "libgen_article",
        "id": 4,
        "books": 0,
        "articles": 1,
        "query_url": "https://libgen.is/scimag/index.php?",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "AAAAARG",
        "url": "http://aaaaarg.fail",
        "code_name": "aaaaarg",
        "id": 5,
        "books": 0,
        "articles": 0,
        "query_url": "http://aaaaarg.fail/search?query=",
        "selected": 0,
        "enabled": 0,
    },
    {
        "full_name": "MLA Commons CORE",
        "url": "https://mla.hcommons.org/deposits/",
        "code_name": "mlacore",
        "id": 6,
        "books": 1,
        "articles": 1,
        "query_url": "https://mla.hcommons.org/wp-admin/admin-ajax.php",
        "selected": 1,
        "enabled": 1,
    },
    {
        "full_name": "SciELO",
        "url": "http://www.scielo.org/",
        "code_name": "scielo",
        "id": 7,
        "books": 0,
        "articles": 1,
        "query_url": "http://search.scielo.org/?q=",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "Memory of The World",
        "url": "https://library.memoryoftheworld.org/",
        "code_name": "memoryoftheworld",
        "id": 8,
        "books": 0,
        "articles": 0,
        "query_url": "https://library.memoryoftheworld.org/",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "Directory of Open Access Journals",
        "url": "https://doaj.org/",
        "code_name": "doaj",
        "id": 9,
        "books": 0,
        "articles": 1,
        "query_url": "http://doaj.org/api/v1/search/articles/",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "Open Science Framework",
        "url": "https://osf.io/search/",
        "code_name": "osf",
        "id": 10,
        "books": 0,
        "articles": 1,
        "query_url": "https://share.osf.io/api/v2/search/creativeworks/_search",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "Unpaywall",
        "url": "https://unpaywall.org/data",
        "code_name": "oadoi",
        "id": 11,
        "books": 0,
        "articles": 1,
        "query_url": "https://api.unpaywall.org/v2/",
        "selected": 1,
        "enabled": 0,
    },
    {
        "full_name": "media/rep/",
        "url": "https://mediarep.org/",
        "code_name": "mediarep",
        "id": 12,
        "books": 1,
        "articles": 1,
        "query_url": "https://mediarep.org/search?spc.page=1&f.itemtype=book,equals",
        "selected": 1,
        "enabled": 0,
    },
]


def load_configs() -> list[ProviderConfig]:
    return [
        ProviderConfig(
            id=r["id"],
            code_name=r["code_name"],
            full_name=r["full_name"],
            url=r["url"],
            query_url=r["query_url"],
            books=bool(r.get("books", True)),
            articles=bool(r.get("articles", False)),
            selected=bool(r.get("selected", True)),
            enabled=bool(r.get("enabled", True)),
        )
        for r in provider_dict]