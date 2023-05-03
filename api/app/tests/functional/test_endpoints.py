import pytest
import json
from app import app

def test_search():
    """ Tests for responses not for accuracy. """
    
    response = app.test_client().get("/v1.0/simple/items?author=foucault&title=society&year=&isbn=&doi=&sources=0+1+2+3+4+6+7+8+9+10+11+12")
    assert response.status_code == 200

    data = json.loads(response.data)

    for d in data:
        assert len(d["bibjson"][0]["title"]) > 0
        assert len(d["bibjson"][0]["link"]) > 0
