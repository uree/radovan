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
  {% if job.results %}
    {% for provider_name, provider_results in job.results.items() %}
      <h3>{{ provider_name }}</h3>
      {% for result in provider_results["items"] %}
        {% set meta = result["bibjson"][0] if result["bibjson"] else {} %}
        {% set extra = result["extra"][0] if result["extra"] else {} %}
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
