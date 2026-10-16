from flask import current_app, render_template, request

from . import web_bp


@web_bp.route("/", methods=["GET"])
def search_page():
    providers = [
        {
            "id": provider.config.id,
            "name": provider.config.full_name,
            "url": provider.config.url,
            "code_name": provider.config.code_name,
        }
        for provider in current_app.extensions["providers"]
    ]
    selected_sources = request.args.getlist("sources", type=int)
    if not selected_sources:
        selected_sources = [provider["id"] for provider in providers]

    return render_template("index.html", providers=providers, selected_sources=selected_sources)


@web_bp.route("/about", methods=["GET"])
def about_page():
    return render_template("about.html")
