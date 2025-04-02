import logging

import requests


logger = logging.getLogger(__name__)


def fetch_provider(provider, url, headers, request_timeout=5, format="json"):
    try:
        request = requests.get(url, timeout=request_timeout)
        request.raise_for_status()
    except requests.exceptions.Timeout:
        logger.debug("The request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.debug(e)
        return None

    if format == "json":
        return request.json()

    if format == "text":
        return request.text
