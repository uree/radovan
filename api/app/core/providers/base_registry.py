from app.core.providers.doab import DOABProvider
from app.core.providers.oapen import OAPENProvider
from app.core.providers.monoskop import MonoskopProvider
from app.core.providers.libgen import LibgenProvider
from app.core.providers.mlacore import MLACOREProvider
from app.core.providers.scielo import ScieloProvider
from app.core.providers.memoryoftheworld import MOTWProvider
from app.core.providers.doaj import DOAJProvider
from app.core.providers.osf import OSFProvider
from app.core.providers.oadoi import UnpaywallProvider

# consider moving into __init__.py
PROVIDERS = {
    "doab": DOABProvider,
    "oapen": OAPENProvider,
    "monoskop": MonoskopProvider,
    "libgen": LibgenProvider,
    "mlacore": MLACOREProvider,
    "scielo": ScieloProvider,
    "memoryoftheworld": MOTWProvider,
    "doaj": DOAJProvider,
    "osf": OSFProvider,
    "oadoi": UnpaywallProvider,
}
