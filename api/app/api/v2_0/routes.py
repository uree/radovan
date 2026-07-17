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


SEARCH_PAGE_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Radovan API search</title>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    <style>
      body { font-family: Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
      label { display: block; margin-top: 0.75rem; }
      input { width: 100%; padding: 0.5rem; box-sizing: border-box; }
      .row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
      .actions { margin-top: 1rem; }
      .panel { margin-top: 1.5rem; padding: 1rem; border: 1px solid #ddd; border-radius: 8px; }
      .muted { color: #666; }
      pre { white-space: pre-wrap; word-break: break-word; }
    </style>
  </head>
  <body>
    <h1>Radovan search</h1>
    <p class="muted">This page uses htmx to call <code>/api/v2.0/search</code> and then polls <code>/api/v2.0/search-job/&lt;job_id&gt;</code>.</p>

    <form
      hx-get="/api/v2.0/search"
      hx-target="#search-response"
      hx-swap="innerHTML"
    >
      <div class="row">
        <label>Author
          <input type="text" name="author">
        </label>
        <label>Title
          <input type="text" name="title">
        </label>
      </div>
      <div class="row">
        <label>Year
          <input type="text" name="year">
        </label>
        <label>ISBN
          <input type="text" name="isbn">
        </label>
      </div>
      <div class="row">
        <label>DOI
          <input type="text" name="doi">
        </label>
        <label>Sources
          <input type="text" name="sources" placeholder="e.g. 1 2 3">
        </label>
      </div>
      <div class="actions">
        <button type="submit">Search</button>
      </div>
    </form>

    <div id="search-response" class="panel">
      <p class="muted">Submit a query to start a search job.</p>
    </div>
  </body>
</html>
"""


SEARCH_STARTED_HTML = """
<div class="panel"
     hx-get="/api/v2.0/search-job/{{ job_id }}"
     hx-trigger="load"
     hx-swap="outerHTML">
  <h2>Search started</h2>
  <p>Job id: <code>{{ job_id }}</code></p>
  <p>Providers: {{ providers|join(', ') }}</p>
  <p class="muted">Loading job status...</p>
</div>
"""


SEARCH_JOB_HTML = """
{% if not job %}
<div class="panel"><p>Job not found.</p></div>
{% elif job.status == "done" %}
<div class="panel">
  <h2>Search complete</h2>
  {% if job.hits %}
    {% for provider_name, provider_hits in job.hits.items() %}
      <h3>{{ provider_name }}</h3>
      {% for result in provider_hits %}
        {% set meta = result.bibjson[0] if result.bibjson else {} %}
        {% set extra = result.extra[0] if result.extra else {} %}
        <div style="margin: 0 0 1rem 0; padding: 0.75rem; border-top: 1px solid #e5e5e5;">
          <div><strong>{{ meta.title or "Untitled" }}</strong></div>
          <div>
            {% if meta.author %}
              {% for author in meta.author %}
                {{ author.name }}{{ ", " if not loop.last }}
              {% endfor %}
            {% else %}
              <span class="muted">No authors listed</span>
            {% endif %}
          </div>
          <div>{{ meta.year or "" }}</div>
          <div>{{ extra.source or provider_name }}</div>
          {% if meta.link %}
            <div>
              {% for link in meta.link %}
                <a href="{{ link.href }}" target="_blank" rel="noopener">{{ link.name or link.href }}</a>{{ " " if not loop.last }}
              {% endfor %}
            </div>
          {% endif %}
        </div>
      {% endfor %}
    {% endfor %}
  {% else %}
    <p>No results found.</p>
  {% endif %}
</div>
<div class="panel">
  <pre>{{ job | tojson(indent=2) }}</pre>
<div>
{% elif job.status == "error" %}
<div class="panel">
  <h2>Search error</h2>
  <p>The search job failed.</p>
</div>
{% else %}
<div class="panel"
     hx-get="/api/v2.0/search-job/{{ job.id }}"
     hx-trigger="load, every 2s"
     hx-swap="outerHTML">
  <h2>Search running</h2>
  <p>Job id: <code>{{ job.id }}</code></p>
  <p>Providers completed: {{ job.providers_completed|length }} / {{ job.providers_total }}</p>
  <p class="muted">Polling for updates...</p>
</div>
{% endif %}
"""


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

    return respond(
        data=response,
        page_template=SEARCH_STARTED_HTML,
        job_id=job_id,
        providers=response.data["providers"],
    )
    
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



# TO DO: what are these two? why are there two?
@api_2_0.route("/sources", methods=["GET"])
def rsources():
    response = ApiResponse()
    response.hits = get_sources()
    return respond(response)
