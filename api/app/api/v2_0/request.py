from typing import Any
import re

from pydantic import BaseModel, Field, field_validator, model_validator
from stdnum import isbn as isbnlib


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
    hit_limit: int = 10
    request_timeout: int = 5

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

        if not isbnlib.is_valid(value):
            raise ValueError("Invalid ISBN")

        return isbnlib.normalize(value)

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



# from dataclasses import dataclass


# @dataclass
# class SearchRequest:
#     author: str = ""
#     title: str = ""
#     year: str = ""
#     isbn: str = ""
#     doi: str = ""
#     sources: list[int] = None

#     def __post_init__(self):
#         self.sources = self.sources or []
    
#     @classmethod
#     def from_args(cls, args):
#         raw = {
#             k: v[0] if len(v) == 1 else v
#             for k, v in args.to_dict(flat=False).items()
#         }
#         return cls(**raw)

#     def validate(self):
#         # at least one non-source field
#         if not any([
#             self.author,
#             self.title,
#             self.year,
#             self.isbn,
#             self.doi,
#         ]):
#             return {
#                 "valid_query": False,
#                 "message": "No valid parameters provided."
#             }

#         # ISBN check
#         if self.isbn:
#             isbn_clean = self.isbn.strip().replace("-", "")
#             if len(isbn_clean) not in (10, 13):
#                 return {
#                     "valid_query": False,
#                     "message": "Invalid ISBN."
#                 }

#         # DOI check
#         if self.doi and not self.doi.startswith("10."):
#             return {
#                 "valid_query": False,
#                 "message": "Misformatted DOI."
#             }

#         return {"valid_query": True}
    

#     def normalize(self):
#         self.author = self.author.strip()
#         self.title = self.title.strip()
#         self.isbn = self.isbn.strip().replace("-", "")

#         if isinstance(self.sources, str):
#             self.sources = [
#                 int(x) for x in self.sources.split() if x.isdigit()
#             ]