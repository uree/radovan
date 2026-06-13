import json

from flask import current_app, request, Blueprint, jsonify
from pydantic import ValidationError

from app.api.v2_0.responses import ApiResponse, respond
from app.api.v2_0.request import SearchRequest
from app.api.utils import is_number
from app.bibjson_methods.methods import mein_main
# from app.core.radovan_core_flexi import search
from app.core.radovan_core_flexi import get_sources
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
    response.message = "Radovan API v2.0 is running. Call /search/single. Try calling /radovan/api/search/single?author=miller&title=&year=2010&isbn=&doi=&sources=2+3. Other valid parameters are author, title, year, doi, isbn, sources"
    return respond(data=response)


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
    
    # TO DO: valiate this as part of SearchRequest? maybe not
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
    return respond(data=response)
    
    # current_app.logger.info(req)
    # current_app.logger.info(req)
    # current_app.logger.info(req.model_dump())

    # search should take the SearchRequest object
    # simple_results = search(req.author, req.title, req.year, req.doi, req.isbn, req.sources)
    
    # this is where the output gets formatted
    # move it inside providers
    # nice_output = mein_main(simple_results)
    # nice_output_sorted = sorted(nice_output["hits"], key=lambda k: k["extra"][0]["rank"])

    # response.hits = nice_output_sorted
    # response.hit_count = len(nice_output_sorted)
    # response.hit_count_per_source =  nice_output["meta"]["hits_per_source"]

    # return jsonify(response.to_dict())


@api_2_0.route("/search-job/<job_id>", methods=["GET"])
def search_status(job_id):
    redis = current_app.extensions["redis"]

    job = get_search_job(redis, job_id)

    if not job:
        respond(ApiResponse(
            message="Not found",
            error="",
            data=None
        ))

    return respond(ApiResponse(message="OK", data=job))



# TO DO: what are these two? why are there two?
@api_2_0.route("/sources", methods=["GET"])
def rsources():
    response = ApiResponse()
    response.hits = get_sources()
    return respond(response)
