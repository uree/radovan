from app.core.providers.doab import DOABProvider
from app.core.providers.mlacore import COREProvider
from app.core.providers.oapen import OAPENProvider
from app.core.providers.monoskop import MonoskopProvider

# consider moving into __ini__.py
PROVIDERS = {
    "doab": DOABProvider,
    "mlacore": COREProvider,
    "oapen": OAPENProvider,
    "monoskop": MonoskopProvider
}
