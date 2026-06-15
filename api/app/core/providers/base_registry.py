from app.core.providers.doab import DOABProvider
from app.core.providers.mlacore import COREProvider
from app.core.providers.oapen import OAPENProvider
from app.core.providers.monoskop import MonoskopProvider
from app.core.providers.libgen_article import LibgenArticleProvider
from app.core.providers.libgen_book import LibgenProvider

# consider moving into __ini__.py
PROVIDERS = {
    "doab": DOABProvider,
    "mlacore": COREProvider,
    "oapen": OAPENProvider,
    "monoskop": MonoskopProvider,
    "libgen_article": LibgenArticleProvider,
    "libgen_book": LibgenProvider,
}
