from abc import ABC, abstractmethod
from typing import Iterable

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from app.core.providers.base_config import ProviderConfig


class Provider(ABC):

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def id(self):
        return self.config.id

    @property
    def code_name(self):
        return self.config.code_name

    @property
    def enabled(self):
        return self.config.enabled

    @abstractmethod
    def search(self, request: SearchRequest) -> Iterable[BibRecord]:
        """
        Full pipeline:
        - fetch data
        - normalize to BibRecord
        - return resuls
        """
    
    def to_bibrecord(self, data):
        record = BibRecord.from_source(data, self.code_name)
        return record

