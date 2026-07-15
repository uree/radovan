from abc import ABC, abstractmethod
import logging
from typing import Iterable

from app.api.v2_0.request import SearchRequest
from app.bibjson_methods.models import BibRecord
from app.core.providers.base_config import ProviderConfig


logger = logging.getLogger(__name__)


class Provider(ABC):

    def __init__(self, config: ProviderConfig, secrets=None):
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
    
    @property
    def supported_params(self):
        return self.config.supported_params

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

    def has_supported_params(self, request: SearchRequest) -> bool:
        logger.debug(self.supported_params)

        attributes = [
            getattr(request, field, None) for field in self.config.supported_params
        ]
        
        logger.debug(attributes)

        return any(
            getattr(request, field, None)
            for field in self.config.supported_params
        )

