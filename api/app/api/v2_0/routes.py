from flask import current_app, request, Blueprint
from pydantic import ValidationError

from app.api.v2_0.responses import ApiResponse, respond
from app.api.v2_0.request import SearchRequest
from app.api.v2_0.test_htmx_templates import SEARCH_PAGE_HTML, SEARCH_JOB_HTML, SEARCH_STARTED_HTML
from app.core.search_service import get_search_job, start_search_job
from app.core.search import search as search


api_2_0 = Blueprint("api_2_0", __name__)


def select_providers(providers, request: SearchRequest):
    if not request.sources:
        return [p for p in providers if p.enabled]

    return [
        p for p in providers
        if p.enabled and p.config.id in request.sources
    ]


@api_2_0.route("/", methods=["GET"])
def hello_world():
    current_app.logger.debug("Debug logger works.")
    response = ApiResponse()
    response.message = "Radovan API v2.0 is running. The search endpoint is at /search."
    return respond(data=response)


@api_2_0.route("/search-page", methods=["GET"])
def search_page():
    response = ApiResponse()
    return respond(response, page_template=SEARCH_PAGE_HTML)


# SEARCH
@api_2_0.route("/search", methods=["GET"])
def search_endpoint():
    response = ApiResponse()
    redis = current_app.extensions["redis"]
    providers = current_app.extensions["providers"]

    try:
        req = SearchRequest.from_args(request.args)
    except ValidationError as e:
        current_app.logger.debug(e.errors())
        response.message = "Invalid request"
        response.error = [err["msg"] for err in e.errors()]
        return respond(response)
    
    # TO DO: check if the validator function in SearchRequest already valdates this
    selected_providers = select_providers(providers, req)
    current_app.logger.debug(f"Selected providers {[n.code_name for n in selected_providers]}")
    if not selected_providers:
        response.message = "Invalid request"
        response.error = "None of the providers selected are enabled"
        return respond(response)
    
    current_app.logger.debug("Starting job ...")
    job_id = start_search_job(redis, selected_providers, req)
    response.data = {
        "job_id": job_id,
        "providers": [p.code_name for p in selected_providers],
    }
    current_app.logger.debug(response.data)

    return respond(
        data=response,
        page_template=SEARCH_STARTED_HTML,
        job_id=job_id,
        providers=response.data["providers"],
    )


@api_2_0.route("/search-job/<job_id>", methods=["GET"])
def search_status(job_id):
    redis = current_app.extensions["redis"]

    job = get_search_job(redis, job_id)

    if not job:
        response = ApiResponse(
            message="Not found",
            error="",
            data=None
        )
        return respond(response, page_template=SEARCH_JOB_HTML, job=None), 404

    return respond(
        ApiResponse(message="OK", data=job),
        page_template=SEARCH_JOB_HTML,
        job=job
    )


@api_2_0.route("/providers", methods=["GET"])
def get_providers():
    providers = [
        provider.config.to_dict() for provider in current_app.extensions["providers"]
    ]
    current_app.logger.debug(providers)
    return respond(ApiResponse(
        message="OK",
        data=providers
    ))
