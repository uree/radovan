from dataclasses import asdict, dataclass, field


@dataclass
class ProviderConfig:
    id: int
    code_name: str
    full_name: str
    url: str
    query_url: str
    selected: bool = True
    enabled: bool = True
    supported_params: list[int] = field(default_factory=list)  # not checking for sources, request_timeout or hit_limit

    def to_dict(self):
        return asdict(self)


DEFAULT_SUPPORTED_PARAMETES = ["author", "title", "year", "doi", "isbn"]
# TO DO: selected should probably be a problem for the interface?
provider_dict = [
    {
        "full_name": "Directory of Open Access Books",
        "url": "https://www.doabooks.org/",
        "code_name": "doab",
        "id": 0,
        "query_url": "https://directory.doabooks.org/rest/search?query=",
        "selected": 1,
        "enabled": 0,
        "supported_params": DEFAULT_SUPPORTED_PARAMETES,
    },
    {
        "full_name": "OAPEN",
        "url": "http://www.oapen.org/home",
        "code_name": "oapen",
        "id": 1,
        "query_url": "https://library.oapen.org/rest/search?query=",
        "selected": 1,
        "enabled": 0,
        "supported_params": DEFAULT_SUPPORTED_PARAMETES,
    },
    {
        "full_name": "Monoskop",
        "url": "https://monoskop.org/",
        "code_name": "monoskop",
        "id": 2,
        "query_url": "https://monoskop.org/log/?cat=17&s=",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["author", "title", "year", "isbn"],
    },
    {
        "full_name": "Library Genesis",
        "url": "https://libgen.li",
        "code_name": "libgen",
        "id": 3,
        "query_url": "https://libgen.li/index.php",
        "selected": 1,
        "enabled": 1,
        "supported_params": DEFAULT_SUPPORTED_PARAMETES,
    },
    {
        "full_name": "AAAAARG",
        "url": "http://aaaaarg.fail",
        "code_name": "aaaaarg",
        "id": 4,
        "query_url": "http://aaaaarg.fail/search?query=",
        "selected": 0,
        "enabled": 0,
    },
    {
        "full_name": "MLA Commons CORE",
        "url": "https://works.hcommons.org/",
        "code_name": "mlacore",
        "id": 5,
        "query_url": "https://works.hcommons.org/api/records",
        "selected": 1,
        "enabled": 1,
        "suported_params": ["author", "title", "year"],
    },
    {
        "full_name": "SciELO",
        "url": "https://www.scielo.org/",
        "code_name": "scielo",
        "id": 6,
        "query_url": "https://search.scielo.org/",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["author", "title", "year", "doi"],
    },
    {
        "full_name": "Memory of The World",
        "url": "https://library.memoryoftheworld.org/",
        "code_name": "memoryoftheworld",
        "id": 7,
        "query_url": "https://library.memoryoftheworld.org/search",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["author", "title"],
    },
    {
        "full_name": "Directory of Open Access Journals",
        "url": "https://doaj.org/",
        "code_name": "doaj",
        "id": 8,
        "query_url": "http://doaj.org/api/v1/search/articles/",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["author", "title", "year", "doi"],
    },
    {
        "full_name": "Open Science Framework",
        "url": "https://osf.io/search/",
        "code_name": "osf",
        "id": 9,
        "query_url": "https://share.osf.io/api/v2/search/creativeworks/_search",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["author", "title", "year"],
    },
    {
        "full_name": "Unpaywall",
        "url": "https://unpaywall.org/data",
        "code_name": "oadoi",
        "id": 10,
        "query_url": "https://api.unpaywall.org/v2/",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["doi"],
    },
    {
        "full_name": "FID Media",
        "url": "https://search.fid-media.de",
        "code_name": "fidmedia",
        "id": 11,
        "query_url": "https://search.fid-media.de/Search/Results",
        "selected": 1,
        "enabled": 1,
        "supported_params": ["author", "title", "year", "isbn"],
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
            selected=bool(r.get("selected", True)),
            enabled=bool(r.get("enabled", True)),
            supported_params=r.get("supported_params", DEFAULT_SUPPORTED_PARAMETES),
        )
        for r in provider_dict]