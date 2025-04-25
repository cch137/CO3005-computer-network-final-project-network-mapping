from flask import Flask, request, Response, jsonify, abort
import cbor2
from embeddings import text_to_embeddings
from constants import PORT

app = Flask(__name__)


def dumped_text_to_embeddings(text: str) -> bytes:
    """
    Convert text to embeddings and serialize to CBOR format.

    Args:
        text (str): The input text to generate embeddings for

    Returns:
        bytes: CBOR serialized embeddings
    """
    return cbor2.dumps(list(text_to_embeddings(text)))


@app.route("/em/", methods=["POST"])
def handle_embedding():
    """
    Handle POST requests to generate text embeddings.
    Supports JSON, URL-encoded form, multipart/form-data, and plain text.

    Returns:
        Response: CBOR-encoded embeddings or error response
    """
    try:
        content_type = request.headers.get("Content-Type", "")
        text = ""
        # Handle different content types
        if content_type.startswith("application/json"):
            json_data = request.get_json()
            if not json_data or "text" not in json_data:
                abort(400, description="Missing 'text' field in JSON")
            text = json_data["text"]
        elif content_type.startswith("application/x-www-form-urlencoded"):
            text = request.form.get("text", "")
        elif content_type.startswith("multipart/form-data"):
            if "text" in request.form:
                text = request.form["text"]
            elif "file" in request.files:
                file = request.files["file"]
                if file.filename:
                    text = file.read().decode("utf-8")
        else:
            # Handle plain text or other content types
            if request.data:
                text = request.data.decode("utf-8")
        if not text:
            abort(400, description="No valid text provided")
        # Generate and return CBOR response
        binary_response = dumped_text_to_embeddings(text)
        return Response(binary_response, content_type="application/cbor", status=200)
    except Exception as e:
        abort(500, description=f"Internal Server Error: {str(e)}")


@app.route("/em/", methods=["GET", "HEAD"])
def method_not_allowed():
    """
    Return 405 Method Not Allowed for GET and HEAD requests.
    """
    abort(405, description="Method Not Allowed")


# ---------- CN-Project API endpoints ----------


@app.route("/cn-project/next-pages", methods=["GET"])
def get_next_pages():
    """
    Mock endpoint for fetching next pages.
    Returns:
        JSON: List of URLs as links
    """
    return jsonify(
        {"links": ["https://example.com/page1", "https://example.com/page2"]}
    )


@app.route("/cn-project/next-nodes", methods=["GET"])
def get_next_nodes():
    """
    Mock endpoint for fetching next nodes.
    Returns:
        JSON: List of domains
    """
    return jsonify({"domains": ["example.com", "another.com"]})


@app.route("/cn-project/store-pages", methods=["POST"])
def store_pages():
    """
    Mock endpoint for storing page metadata.
    Accepts JSON or form URL-encoded data.

    Returns:
        JSON: Success status
    """
    content_type = request.headers.get("Content-Type", "")
    if not (
        content_type.startswith("application/json")
        or content_type.startswith("application/x-www-form-urlencoded")
    ):
        abort(415, description="Unsupported Content-Type")
    return jsonify({"success": True})


@app.route("/cn-project/store-nodes", methods=["POST"])
def store_nodes():
    """
    Mock endpoint for storing node data.
    Accepts JSON or form URL-encoded data.

    Returns:
        JSON: Success status
    """
    content_type = request.headers.get("Content-Type", "")
    if not (
        content_type.startswith("application/json")
        or content_type.startswith("application/x-www-form-urlencoded")
    ):
        abort(415, description="Unsupported Content-Type")
    return jsonify({"success": True})


@app.errorhandler(400)
@app.errorhandler(405)
@app.errorhandler(415)
@app.errorhandler(500)
def handle_error(error):
    """
    Custom error handler for HTTP errors.

    Args:
        error: The error object containing code and description

    Returns:
        Response: JSON error response
    """
    return jsonify({"error": str(error.description), "status": error.code}), error.code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
