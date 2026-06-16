from app.core.providers.doab import DOABProvider
from app.core.providers.oapen import OAPENProvider
from app.core.providers.monoskop import MonoskopProvider
from app.core.providers.libgen import LibgenProvider
from app.core.providers.mlacore import MLACOREProvider
from app.core.providers.scielo import ScieloProvider

# consider moving into __init__.py
PROVIDERS = {
    "doab": DOABProvider,
    "oapen": OAPENProvider,
    "monoskop": MonoskopProvider,
    "libgen": LibgenProvider,
    "mlacore": MLACOREProvider,
    "scielo": ScieloProvider,
}
