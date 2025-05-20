from flask import Flask, request, Response, jsonify, abort
import cbor2
import threading
from pydantic import ValidationError
from modules.embeddings import text_to_embeddings
from modules.schemas import NodeSchema, PageSchema
from modules.collection import ChunkCollection
from modules.logger import logger
from modules.database import (
    insert_pages,
    insert_nodes,
    get_top_unvisited_domains,
    get_top_unvisited_urls,
)
from modules.constants import PORT, IS_PRODUCTION_ENV

app = Flask(__name__)


def dumped_text_to_embeddings(text: str) -> bytes:
    """
    Converts text to embeddings and serializes to CBOR format.

    Args:
        text: Input text for embedding generation.

    Returns:
        CBOR-serialized embeddings as bytes.
    """
    return cbor2.dumps(list(text_to_embeddings(text)))


@app.route("/")
def handle_home():
    return Response("OK", content_type="text/plain", status=200)


@app.route("/vectors", methods=["POST"])
def handle_embedding():
    """
    Processes POST requests to generate text embeddings.
    Supports JSON, URL-encoded form, multipart/form-data, and plain text content types.

    Returns:
        Flask Response with CBOR-encoded embeddings or an error response.
    """
    try:
        content_type = request.headers.get("Content-Type", "")
        text = ""
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
            if request.data:
                text = request.data.decode("utf-8")
        if not text:
            abort(400, description="No valid text provided")
        binary_response = dumped_text_to_embeddings(text)
        return Response(binary_response, content_type="application/cbor", status=200)
    except Exception as e:
        abort(500, description=f"Internal Server Error: {str(e)}")


# ---------- CN-Project API Endpoints ----------

chunks = ChunkCollection("chunks")

lock = False


@app.route("/cn-project/lock", methods=["GET"])
def get_lock():
    return jsonify({"lock": lock})


@app.route("/cn-project/next-pages", methods=["GET"])
def get_next_pages():
    """
    Retrieves the next unvisited pages.

    Returns:
        JSON response containing a list of URLs.
    """
    return jsonify({"links": get_top_unvisited_urls()})


@app.route("/cn-project/next-domains", methods=["GET"])
def get_next_nodes():
    """
    Retrieves the next unvisited domains.

    Returns:
        JSON response containing a list of domains.
    """
    return jsonify({"domains": get_top_unvisited_domains()})


def process_page_content(inserted_pages):
    """
    Process page content in a separate thread.
    Sets the global lock while processing.

    Args:
        inserted_pages: Dictionary of page UUIDs to Page objects
    """
    global lock
    lock = True
    try:
        for page_uuid, page in inserted_pages.items():
            try:
                chunks.write_content(page_uuid, page.markdown)
            except Exception as e:
                logger.error(f"Failed to insert content for page {page_uuid}: {str(e)}")
    finally:
        lock = False


@app.route("/cn-project/store-pages", methods=["POST"])
def store_pages():
    """
    Stores page metadata and processes content chunks in the background.
    Expects a JSON array validated against PageSchema.

    The content processing happens in a separate thread to avoid blocking the response.
    If the system is currently locked, returns an error response.

    Returns:
        JSON response indicating success or validation errors.
    """
    # Check if the system is currently locked
    global lock
    if lock:
        return (
            jsonify(
                {
                    "success": False,
                    "errors": "System is currently processing content. Try again later.",
                }
            ),
            429,
        )

    content_type = request.headers.get("Content-Type", "")
    if not content_type.startswith("application/json"):
        abort(415, description="Unsupported Content-Type")

    try:
        pages_json = request.get_json()
        if not isinstance(pages_json, list):
            return (
                jsonify({"success": False, "errors": "Expected a list of pages"}),
                422,
            )

        pages = [PageSchema.model_validate(item) for item in pages_json]
    except ValidationError as e:
        return jsonify({"success": False, "errors": e.errors()}), 422

    inserted_pages = insert_pages(pages)

    # Start a new thread to process the content
    threading.Thread(
        target=process_page_content, args=(inserted_pages,), daemon=True
    ).start()

    return jsonify({"success": True})


@app.route("/cn-project/store-nodes", methods=["POST"])
def store_nodes():
    """
    Stores node metadata.
    Expects a JSON array validated against NodeSchema.

    Returns:
        JSON response indicating success or validation errors.
    """
    content_type = request.headers.get("Content-Type", "")
    if not content_type.startswith("application/json"):
        abort(415, description="Unsupported Content-Type")

    try:
        nodes_json = request.get_json()
        if not isinstance(nodes_json, list):
            return (
                jsonify({"success": False, "errors": "Expected a list of nodes"}),
                422,
            )

        nodes = [NodeSchema.model_validate(item) for item in nodes_json]
    except ValidationError as e:
        return jsonify({"success": False, "errors": e.errors()}), 422

    insert_nodes(nodes)
    return jsonify({"success": True})


@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(404)
@app.errorhandler(415)
@app.errorhandler(500)
def handle_error(error):
    """
    Handles HTTP errors with custom JSON responses.

    Args:
        error: Error object containing code and description.

    Returns:
        JSON response with error status and description.
    """
    return jsonify({"status": error.code, "error": str(error.description)}), error.code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=IS_PRODUCTION_ENV)
