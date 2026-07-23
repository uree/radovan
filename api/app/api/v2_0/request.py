import logging
from typing import Any
import re

from pydantic import BaseModel, Field, field_validator, model_validator  # using pydantic here because of validation functionalities
from stdnum import isbn as isbnlib


logger = logging.getLogger(__name__)
DOI_RE = re.compile(
    r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$",
    re.I,
)


class SearchRequest(BaseModel):
    author: str = ""
    title: str = ""
    year: str = ""
    isbn: str = ""
    doi: str = ""
    format: str = ""
    hit_limit: int = Field(default=10, ge=1, le=20)
    request_timeout: int= Field(default=5, ge=1, le=20)

    sources: list[int] = Field(default_factory=list)

    @classmethod
    def from_args(cls, args: Any) -> "SearchRequest":
        raw = {
            k: v[0] if len(v) == 1 else v
            for k, v in args.to_dict(flat=False).items()
        }

        return cls.model_validate(raw)

    @field_validator("author", "title", "year", "doi", mode="before")
    @classmethod
    def strip_strings(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("isbn", mode="before")
    @classmethod
    def normalize_isbn(cls, value):
        if not value:
            return ""

        value = value.strip()
        value = isbnlib.compact(value)

        if not isbnlib.is_valid(value):
            raise ValueError("Invalid ISBN")

        logger.debug(dir(isbnlib))

        return value

    @field_validator("doi")
    @classmethod
    def validate_doi(cls, value):
        if value and not DOI_RE.match(value):
            raise ValueError("Misformatted DOI")

        return value

    @field_validator("sources", mode="before")
    @classmethod
    def normalize_sources(cls, value):
        if value is None:
            return []

        if isinstance(value, str):
            return [
                int(x)
                for x in value.split()
                if x.isdigit()
            ]

        if isinstance(value, list):
            return [
                int(x)
                for x in value
            ]

        return value

    @model_validator(mode="after")
    def validate_query(self):
        if not any([
            self.author,
            self.title,
            self.year,
            self.isbn,
            self.doi,
        ]):
            raise ValueError(
                "At least one search parameter must be provided"
            )

        return self
