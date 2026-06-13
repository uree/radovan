from app.core.providers.doab import DOABProvider
from app.core.providers.mlacore import COREProvider
from app.core.providers.oapen import OAPENProvider

# consider moving into __ini__.py
PROVIDERS = {
    "doab": DOABProvider,
    "mlacore": COREProvider,
    "oapen": OAPENProvider
}
