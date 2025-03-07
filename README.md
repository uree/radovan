# Radovan from planet Meta
a meta search engine for the commons

Radovan is a meta search engine aggregating 12 open access sources of (mostly academic) texts:

- [Directory of Open Access Books](https://www.doabooks.org/)
- [OAPEN](http://www.oapen.org/home)
- [Monoskop](https://monoskop.org/Monoskop)
- [Library Genesis](http://gen.lib.rus.ec/)
- [Library Genesis Scimag](http://gen.lib.rus.ec/scimag/index.php)
- [AAAAARG](http://aaaaarg.fail)
- [MLA Commons CORE](https://mla.hcommons.org/deposits)
- [SciELO](http://www.scielo.org/)
- [Memory of the World](http://library.memoryoftheworld.org)
- [Directory of Open Access Journals](https://doaj.org/)
- [Open Science Framework Preprints](https://osf.io/search/)
- [Unpaywall](https://unpaywall.org/data)

There is a of sources waiting to be added in PROVIDERS.md. Open an issue to suggest more.

A live version is available [here](https://yurisearch.postdigitalcultures.org/radovan/). Along with [additional information](https://yurisearch.postdigitalcultures.org/radovan/about), including on how to use the API.

The results inherit the order in which they are displayed on the original page and are grouped accordingly. This instance of Radovan currently harvests 10 hits per source. This can be changed in the settings section on top of radovan_core_flexi.py.

## Deployment

The easiest way to run your own instance is to use docker(-compose).

```
cd api
docker-compose up -d
cd iface
docker-compose up -d
```

This will start the API at port 9003 and the interface at port 9090.

To be able to search [aaaaarg](https://aaaaarg.fail/), create a file called keys.py in api/app/ and save your login info as yarr_user and yarr_pass.
To be able to search [oadoi/unpaywall](https://api.unpaywall.org/v2/), you need to enter your email address in the same file under oadoi_email.


## Development

To use the profiler in `radovan_core_flexi.py`, place `@profile` in front of the function you want to analyse.

Run tests inside the `app` folder.  Use `python -m pytest -sv` for verbose output with logging included (in case debugging is needed).
