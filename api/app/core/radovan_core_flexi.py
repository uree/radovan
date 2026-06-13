import logging
import pprint

from flask import current_app

from multiprocessing import Process, Queue

# from .providers.aaaaarg import aaaaarg  # noqa
from .providers.core import core  # noqa
# from .providers.doab import doab  # noqa
from .providers.doaj import doaj  # noqa
from .providers.libgen_article import libgen_article  # noqa
from .providers.libgen_book import libgen_book  # noqa
from .providers.mediarep import mediarep  # noqa
from .providers.memoryoftheworld import memoryoftheworld  # noqa
from .providers.monoskop import monoskop  # noqa
from .providers.oadoi import oadoi  # noqa
from .providers.oapen import oapen  # noqa
from .providers.osf import osf  # noqa
from .providers.scielo import scielo  # noqa

from .sources import sources_dict  # to object?
from .utils import is_number


logger = logging.getLogger(__name__)


def get_sources(disabled=False):
    if not disabled:
        return [n for n in sources_dict if n['enabled']]

    return sources_dict


def map_sources_to_ids(sources, sources_dict):
    if isinstance(sources, list) and not is_number(sources[0]):
        return [
            next(n['id'] for n in sources_dict if n['code_name'] == s)
            for s in sources
        ]
    return sources


def search(
    author='',
    title='',
    year='',
    doi='',
    isbn='',
    sources='',
    hit_limit=10,
    aaaaarg_browser=None
):

    # can do without all this validation now (pydantic)
    output_dict = {'entries': []}
    author, title, year, doi = (arg.strip() for arg in (author, title, year, doi))
    isbn = isbn.strip().replace('-', '')

    try:
        sources = sources.split(' ')
    except Exception as e:
        logger.debug(f"Sources already a list: {e}")
        pass

    # what is the point of this?
    sources = map_sources_to_ids(sources, sources_dict)
    logger.debug(sources)

    # remove aaaarg from list of sources if login unsuccessful
    if aaaaarg_browser is None and 5 in sources:
        sources.remove(5)

    selection = [n['code_name'] for n in sources_dict if n['id'] in sources and n['enabled']]

    logger.debug(selection)

    # callables?
    possibles = globals().copy()
    possibles.update(locals())
    logger.debug(possibles)

    result_queue = Queue()
    proc = []
    results = []

    for fn in selection:
        # special treatment for aaaaarg is necessary because of different parameters
        if fn == 'aaaaarg':
            p = Process(
                target=possibles.get(fn),
                args=(result_queue, aaaaarg_browser, author, title, hit_limit)
            )
        else:
            p = Process(
                target=possibles.get(fn),
                args=(result_queue, author, title, year, doi, isbn, hit_limit)
            )

        p.start()
        proc.append(p)

    # pull the data out of the queue before the join
    for p in proc:
        item = result_queue.get()
        output_dict['entries'].append(item)

    for p in proc:
        p.join()

    return output_dict
