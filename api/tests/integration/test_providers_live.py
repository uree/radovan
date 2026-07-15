from app.api.v2_0.request import SearchRequest
from app.config import Config
from app.core.providers.base_config import ProviderConfig
from app.core.providers.doab import DOABProvider
from app.core.providers.oapen import OAPENProvider
from app.core.providers.monoskop import MonoskopProvider
from app.core.providers.libgen import LibgenProvider
from app.core.providers.mlacore import MLACOREProvider
from app.core.providers.scielo import ScieloProvider
from app.core.providers.memoryoftheworld import MOTWProvider
from app.core.providers.doaj import DOAJProvider
from app.core.providers.osf import OSFProvider
from app.core.providers.oadoi import UnpaywallProvider


def test_doab_live():
    provider = DOABProvider(
        ProviderConfig(
            id=0,
            code_name="doab",
            full_name="Directory of Open Access Books",
            url="https://www.doabooks.org/",
            query_url="https://directory.doabooks.org/rest/search?query=",
        )
    )

    request = SearchRequest(
        title="memory",
        hit_limit=3,
        request_timeout=10,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "doab"

    assert bibjson.get("title")
    assert bibjson.get("link")


def test_oapen_live():
    provider = OAPENProvider(
        ProviderConfig(
            id=1,
            code_name="oapen",
            full_name="OAPEN",
            url="http://www.oapen.org/home",
            query_url="https://library.oapen.org/rest/search?query=",
        )
    )

    request = SearchRequest(
        title="memory",
        hit_limit=3,
        request_timeout=10,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "oapen"
    assert bibjson.get("title")
    assert bibjson.get("link")


def test_monoskop_live():
    provider =MonoskopProvider(
        ProviderConfig(
            id=1,
            code_name="monoskop",
            full_name="Monoskop",
            url="https://monoskop.org/Monoskop",
            query_url="https://monoskop.org/log/?cat=17&s=",
        )
    )

    request = SearchRequest(
        author="tomislav medak",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "monoskop"
    assert bibjson.get("title")
    assert bibjson.get("link")


def test_libgen_live():
    provider =LibgenProvider(
        ProviderConfig(
            id=1,
            code_name="libgen",
            full_name="Library Genesis",
            url="https://libgen.vg",
            query_url="https://libgen.vg/index.php",
        )
    )

    request = SearchRequest(
        author="donna haraway",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "libgen"
    assert bibjson.get("title")


def test_mlacore_live():
    provider = MLACOREProvider(
        ProviderConfig(
            id=1,
            code_name="mlacore",
            full_name="MLA Commons CORE",
            url="https://works.hcommons.org/",
            query_url="https://works.hcommons.org/api/records",
        )
    )

    request = SearchRequest(
        author="senchyne",
        title="money",
        year="2017",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "mlacore"
    assert bibjson.get("title")
    assert bibjson.get("author")
    assert bibjson.get("link")
    assert extra.get("landing_url")


def test_scielo_live():
    provider = ScieloProvider(
        ProviderConfig(
            id=6,
            code_name="scielo",
            full_name="SciELO",
            url="https://www.scielo.org/",
            query_url="https://search.scielo.org/",
        )
    )

    request = SearchRequest(
        author="jesus",
        title="mapuche",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "scielo"
    assert bibjson.get("title")
    assert bibjson.get("author")
    assert bibjson.get("link")
    assert extra.get("download_url")


def test_memoryoftheworld_live():
    provider = MOTWProvider(
        ProviderConfig(
            id=7,
            code_name="memoryoftheworld",
            full_name="Memory of The World",
            url="https://library.memoryoftheworld.org/",
            query_url="https://library.memoryoftheworld.org/search",
        )
    )

    request = SearchRequest(
        author="adorno",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "memoryoftheworld"
    assert bibjson.get("title")
    assert bibjson.get("author")

    request = SearchRequest(
        title="playing the whore",
        hit_limit=3,
    )

    results = provider.search(request)

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "memoryoftheworld"
    assert bibjson.get("title")
    assert bibjson.get("author")


def test_doaj_live():
    provider = DOAJProvider(
        ProviderConfig(
            id=8,
            code_name="doaj",
            full_name="Directory of Open Access Journals",
            url="https://doaj.org/",
            query_url="http://doaj.org/api/v1/search/articles/",
        )
    )

    request = SearchRequest(
        title="money",
        author="appelt",
        year="2017",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "doaj"
    assert bibjson.get("title")
    assert bibjson.get("author")

    request = SearchRequest(
        doi="10.18096/TMP.2017.01.01",
        hit_limit=3,
    )
    
    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "doaj"
    assert bibjson.get("title")
    assert bibjson.get("author")


def test_osf_live():
    provider = OSFProvider(
        ProviderConfig(
            id=9,
            code_name="osf",
            full_name="Open Science Framework",
            url="https://osf.io/search/",
            query_url="https://share.osf.io/api/v2/search/creativeworks/_search",
            supported_params=["author", "title", "year"],
        )
    )

    request = SearchRequest(
        title="inequality",
        author="boyd",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "osf"
    assert bibjson.get("title")
    assert bibjson.get("author")


def test_oadoi_live():
    # derp
    secrets = {"OADOI_EMAIL": None}
    secrets["OADOI_EMAIL"] = Config.OADOI_EMAIL

    provider = UnpaywallProvider(
        ProviderConfig(
            id=10,
            code_name="oadoi",
            full_name="Unpaywall",
            url="https://unpaywall.org/data",
            query_url="https://api.unpaywall.org/v2/",
            supported_params=["doi"],
        ),
        secrets=secrets
    )

    request = SearchRequest(
        doi="10.1038/nature12373",
        hit_limit=3,
    )

    results = list(provider.search(request))

    assert len(results) > 0

    record = results[0]
    assert "bibjson" in record
    assert "extra" in record

    bibjson = record["bibjson"][0]
    extra = record["extra"][0]

    assert extra["source"] == "oadoi"
    assert bibjson.get("title")
    assert bibjson.get("author")
    assert bibjson.get("link")