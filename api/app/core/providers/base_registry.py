from app.core.providers.doab import DOABProvider
from app.core.providers.mlacore import COREProvider

# consider moving into __ini__.py
PROVIDERS = {
    "doab": DOABProvider,
    "mlacore": COREProvider,
}
