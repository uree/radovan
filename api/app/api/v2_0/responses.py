from dataclasses import asdict, dataclass

from flask import jsonify, render_template_string, request


@dataclass
class ApiResponse:
    message: str = "OK"
    error: str | None = None
    data: object = None

    def to_dict(self):
        return asdict(self)


# TO DO: if need be implement partial template suport
def respond(data: ApiResponse, page_template: str | None = None, **kwargs):
    """ Resolve what to return based on request, html or json. 

    Kwargs for other variables needed for rendering the template (potentially).
    """

    if request.args.get("format") == "json":
        return jsonify(data.to_dict())
    
    if request.headers.get("HX-Request"):
        return render_template_string(
            page_template,
            **data.to_dict(),
            **kwargs,
        )
    
    return render_template_string(
        page_template,
        **data.to_dict(),
        **kwargs,
    )

