from app.core.providers.doab import DOABProvider
from app.core.providers.core import COREProvider

# consider moving into __ini__.py
PROVIDERS = {
    "doab": DOABProvider,
    "core": COREProvider,
}
