import pytest  # noqa
from core.radovan_core_flexi import search


def test_doab():
    results = search(title="memory", sources=[0])

    assert len(results["entries"][0]["doab"]["hits"]) > 0
    assert len(results["entries"][0]["doab"]["hits"][0]["dc.title"]) > 0
    assert "memory" in results["entries"][0]["doab"]["hits"][0]["dc.description.abstract"]


def test_oapen():
    results = search(title="memory", sources=[1])

    assert len(results["entries"][0]["oapen"]["hits"]) > 0
    assert len(results["entries"][0]["oapen"]["hits"][0]["dc.title"]) > 0
    assert "memory" in results["entries"][0]["oapen"]["hits"][0]["dc.description.abstract"]


def test_libgen():
    results = search(author="donna haraway", sources=[3])

    assert len(results["entries"][0]["libgen_book"]["hits"]) > 0
    assert len(results["entries"][0]["libgen_book"]["hits"][0]["title"]) > 0
    assert results["entries"][0]["libgen_book"]["hits"][1]["author"] == "Donna J. Haraway"


def test_libgen_article():
    results = search(author="Stefano Harney", sources=[4])

    assert len(results["entries"][0]["libgen_article"]["hits"]) > 0
    assert len(results["entries"][0]["libgen_article"]["hits"][0]["title"]) > 0
    assert "Stefano Harney" in results["entries"][0]["libgen_article"]["hits"][0]["author"]


def test_mla_core():
    results = search(title="fashion", sources=[6])

    assert len(results["entries"][0]["core"]["hits"]) > 0
    assert len(results["entries"][0]["core"]["hits"][0]["title"]) > 0
    # the results returned from mla core are not consistent, they get ranked differently every time


def test_scielo():
    results = search(title="cannabis", sources=[7])

    assert len(results["entries"][0]["scielo"]["hits"]) > 0
    assert len(results["entries"][0]["scielo"]["hits"][0]["TI"]) > 0
    assert "cannabis" in results["entries"][0]["scielo"]["hits"][0]["AB"].lower()


def test_memoryoftheworld():
    results = search(author="tomislav medak", sources=[8])

    assert len(results["entries"][0]["memoryoftheworld"]["hits"]) > 0
    assert len(results["entries"][0]["memoryoftheworld"]["hits"][0]["title"]) > 0
    assert "Tomislav Medak" in results["entries"][0]["memoryoftheworld"]["hits"][0]["author"]


def test_doaj():
    results = search(title="memory", sources=[9])

    assert len(results["entries"][0]["doaj"]["hits"]) > 0
    assert len(results["entries"][0]["doaj"]["hits"][0]["bibjson"]["title"]) > 0
    assert "memory" in results["entries"][0]["doaj"]["hits"][0]["bibjson"]["abstract"]


def test_osf():
    results = search(title="memory", sources=[10])

    assert len(results["entries"][0]["osf"]["hits"]) > 0
    assert len(results["entries"][0]["osf"]["hits"][0]["title"]) > 0
    assert "memory" in results["entries"][0]["osf"]["hits"][0]["title"].lower()


def test_unpaywall():  # aka oadoi
    results = search(doi="10.1038/nature12373", sources=[11])

    assert len(results["entries"][0]["oadoi"]["hits"]) > 0
    assert len(results["entries"][0]["oadoi"]["hits"][0]["title"]) > 0
    assert "thermometry" in results["entries"][0]["oadoi"]["hits"][0]["title"].lower()

    results = search(title="cannabis", sources=[11])
    assert len(results["entries"][0]["oadoi"]["hits"]) > 0
    assert len(results["entries"][0]["oadoi"]["hits"][0]["title"]) > 0
    assert "cannabis" in results["entries"][0]["oadoi"]["hits"][0]["title"].lower()


def test_mediarep():
    results = search(title="revolution", sources=[12])

    assert len(results["entries"][0]["mediarep"]["hits"]) > 0
    assert len(results["entries"][0]["mediarep"]["hits"][0]["title"]) > 0
    assert "revolution" in results["entries"][0]["mediarep"]["hits"][0]["title"].lower()
