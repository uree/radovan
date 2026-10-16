# Radovan from planet Meta
a meta search engine for the commons

Radovan is a meta search engine aggregating a number of open access sources of (mostly academic) texts:

- [Directory of Open Access Books](https://www.doabooks.org/) (not working)
- [OAPEN](http://www.oapen.org/home) (not working)
- [Monoskop](https://monoskop.org/Monoskop)
- [Library Genesis](http://gen.lib.rus.ec/)
- [AAAAARG](http://aaaaarg.fail)
- [MLA Commons CORE](https://mla.hcommons.org/deposits)
- [SciELO](http://www.scielo.org/)
- [Memory of the World](http://library.memoryoftheworld.org)
- [Directory of Open Access Journals](https://doaj.org/)
- [Open Science Framework Preprints](https://osf.io/search/)
- [Unpaywall](https://unpaywall.org/data)
- [FID Media](https://search.fid-media.de)

There is a of sources waiting to be added in PROVIDERS.md. Open an issue to suggest more.

A live version is not available atm. 

The results inherit the order in which they are displayed on the original page and are grouped accordingly. 

## Deployment

The easiest way to run your own instance is with Docker Compose.

For local development:

```bash
docker compose -f compose.yml -f compose.dev.yml up --build
```

The development server is available at <http://localhost:9003> and reloads when source files change.

For staging or production, specify the env file. Check `.env.example` for reference.

```bash
docker compose --env-file production.env \
  -f compose.yml -f compose.prod.yml up -d --build
```

Staging and production use Gunicorn and include configurable CPU and memory limits.


## Roadmap (excluding adding more providers)

- [ ] refactor bibjson_methods and offer metadata imports to zotero
- [ ] more useful and reliable url classification
- [ ] uptime monitor for services
- [ ] group results per rank, not provider
