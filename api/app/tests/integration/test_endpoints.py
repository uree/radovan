import pytest
import json
from app import app
from core.sources import sources_dict


def test_search():
    """ Tests for responses not for accuracy. Tests enabled sources only. """

    selection = "+".join([str(n["id"]) for n in sources_dict if n["enabled"]])
    print(selection)

    response = app.test_client().get(f"/v1.0/simple/items?author=memory&title=&year=&isbn=&doi=&sources={selection}")  # noqa:E501
    assert response.status_code == 200

    data = json.loads(response.data)

    for d in data:
        assert len(d["bibjson"][0]["link"]) > 0
