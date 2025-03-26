import pytest
from app import *
from core.radovan_core_flexi import *


def test_doab():
    results = new_combined(title="memory", sources=[0])

    assert len(results[0]["doab"]["hits"]) > 0
    assert len(results[0]["doab"]["hits"][0]["dc.title"]) > 0
    assert "memory" in results[0]["doab"]["hits"][0]["dc.description.abstract"]


def test_oapen():
    results = new_combined(title="memory", sources=[1])

    assert len(results[0]["oapen"]["hits"]) > 0
    assert len(results[0]["oapen"]["hits"][0]["dc.title"]) > 0
    assert "memory" in results[0]["oapen"]["hits"][0]["dc.description.abstract"]


def test_libgen():
    results = new_combined(author="donna haraway", sources=[3])

    assert len(results[0]["libgen_book"]["hits"]) > 0
    assert len(results[0]["libgen_book"]["hits"][0]["title"]) > 0
    assert results[0]["libgen_book"]["hits"][1]["author"] == "Donna J. Haraway"


def test_libgen_article():
    results = new_combined(author="Stefano Harney", sources=[4])

    assert len(results[0]["libgen_article"]["hits"]) > 0
    assert len(results[0]["libgen_article"]["hits"][0]["title"]) > 0
    assert "Stefano Harney" in results[0]["libgen_article"]["hits"][0]["author"]


def test_mla_core():
    results = new_combined(title="fashion", sources=[6])

    assert len(results[0]["core"]["hits"]) > 0
    assert len(results[0]["core"]["hits"][0]["title"]) > 0
    # the results returned from mla core are not consistent, they get ranked differently every time


def test_scielo():
    results = new_combined(title="synthesis", sources=[7])

    assert len(results[0]["scielo"]["hits"]) > 0
    assert len(results[0]["scielo"]["hits"][0]["TI"]) > 0
    assert "synthesis" in results[0]["scielo"]["hits"][0]["AB"].lower()


def test_memoryoftheworld():
    results = new_combined(author="tomislav medak", sources=[8])

    assert len(results[0]["memoryoftheworld"]["hits"]) > 0
    assert len(results[0]["memoryoftheworld"]["hits"][0]["title"]) > 0
    assert "Tomislav Medak" in results[0]["memoryoftheworld"]["hits"][0]["author"]


def test_doaj():
    results = new_combined(title="memory", sources=[9])

    assert len(results[0]["doaj"]["hits"]) > 0
    assert len(results[0]["doaj"]["hits"][0]["bibjson"]["title"]) > 0
    assert "memory" in results[0]["doaj"]["hits"][0]["bibjson"]["abstract"]


def test_osf():
    results = new_combined(title="memory", sources=[10])

    assert len(results[0]["osf"]["hits"]) > 0
    assert len(results[0]["osf"]["hits"][0]["title"]) > 0
    assert "memory" in results[0]["osf"]["hits"][0]["description"]


def test_unpaywall():
    results = new_combined(doi="10.1038/nature12373", sources=[11])

    assert len(results[0]["oadoi"]["hits"]) > 0
    assert len(results[0]["oadoi"]["hits"][0]["title"]) > 0
    assert "thermometry" in results[0]["oadoi"]["hits"][0]["title"]


def test_mediarep():
    results = new_combined(title="revolution", sources=[12])

    assert len(results[0]["mediarep"]["hits"]) > 0
    assert len(results[0]["mediarep"]["hits"][0]["title"]) > 0
    assert "revolution" in results[0]["mediarep"]["hits"][0]["title"].lower()
