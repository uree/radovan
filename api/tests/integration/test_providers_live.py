from app.api.v2_0.request import SearchRequest
from app.core.providers.base_config import ProviderConfig
from app.core.providers.doab import DOABProvider
from app.core.providers.oapen import OAPENProvider
from app.core.providers.monoskop import MonoskopProvider


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