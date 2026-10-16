from concurrent.futures import ThreadPoolExecutor, as_completed

from app.api.v2_0.request import SearchRequest


# TO DO: decide what data structure to return here
def search(providers, request: SearchRequest) -> dict:
    """
    Run search across all enabled providers (built at app startup)
    and aggregate results.
    """

    with ThreadPoolExecutor(max_workers=len(providers)) as executor:

        future_to_provider = {
            executor.submit(provider.search, request): provider
            for provider in providers
        }

        for future in as_completed(future_to_provider):

            provider = future_to_provider[future]

            try:
                results = future.result()

                yield {
                    "provider": provider.code_name,
                    "status": "ok",
                    "results": results.to_dict(),
                }

            except Exception as e:  # noqa: BLE001
                yield {
                    "provider": provider.code_name,
                    "status": "error",
                    "error": str(e),
                    "results": [],
                }