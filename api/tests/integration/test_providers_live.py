from app.api.v2_0.request import SearchRequest
from app.core.providers.base_config import ProviderConfig
from app.core.providers.doab import DOABProvider


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
    assert "rank" not in extra

    assert bibjson.get("title")
    assert bibjson.get("link")