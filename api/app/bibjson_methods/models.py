from dataclasses import dataclass, asdict
from typing import Optional, List

from .methods import process_hit
from .settings import bibjson_aliases, extra_aliases, types
from .utils import flatten_dict_values


@dataclass
class BibRecord:
    bibjson: dict
    extra: dict

    # TO DO (in the future)
    # better = cannonical representation (much more refactoring)
    # sketch at the bottom of the file
    # & then when converting to bibjson
    # split into bibjson & extra


    @classmethod
    def from_source(
        cls,
        hit_data,
        source,
        extra_aliases=extra_aliases,
        bibjson_aliases=bibjson_aliases,
        types=types,
    ):
        extra_aliases_flat = flatten_dict_values(extra_aliases)
        bibjson_aliases_flat = flatten_dict_values(bibjson_aliases)
        hit = process_hit(
                hit_data,
                source,
                extra_aliases_flat,
                bibjson_aliases_flat,
                types
            )

        return cls(
            bibjson=hit["bibjson"],
            extra=hit["extra"]
        )
    
    def to_dict(self):
        return asdict(self)


# sample canonical representation
# @dataclass
# class BibRecord:
#     type: str = "misc"

#     # string fields
#     title: str | None = None
#     abstract: str | None = None
#     journal: str | None = None
#     publisher: str | None = None
#     year: str | None = None
#     volume: str | None = None
#     number: str | None = None
#     pages: str | None = None

#     # collections
#     author: list[dict] = field(default_factory=list)
#     editor: list[dict] = field(default_factory=list)
#     identifier: list[dict] = field(default_factory=list)
#     link: list[dict] = field(default_factory=list)
#     subject: list[dict] = field(default_factory=list)

#     # unmapped source-specific data
#     extra: dict = field(default_factory=dict)

# BibRecord method converts to this, optionally
# @dataclass
# class BibJSONRecord:
#     title: str
#     authors: List[str]
#     source: str

#     url: Optional[str] = None
#     year: Optional[str] = None
#     doi: Optional[str] = None

#     def to_dict(self):
#         return asdict(self)