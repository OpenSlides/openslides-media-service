from flask import Flask, jsonify, request

app = Flask(__name__)

app.logger.info("Started Dummy-Autoupdate")


# for testing
@app.route("/internal/autoupdate", methods=["POST"])
def dummy_autoupdate():
    app.logger.debug(f"dummy_autoupdate gets: {request.json}")
    file_id = request.json[0]["ids"][0]

    # Valid response from autoupdate, but not found in DB
    if file_id == 1:
        return jsonify(
            {
                f"mediafile/{file_id}/id": file_id,
                f"mediafile/{file_id}/filename": "Does not exist",
            }
        )

    # OK-cases for dummy data
    if file_id == 2:
        return jsonify(
            {
                f"mediafile/{file_id}/id": file_id,
                f"mediafile/{file_id}/filename": "A.txt",
            }
        )
    if file_id == 3:
        return jsonify(
            {
                f"mediafile/{file_id}/id": file_id,
                f"mediafile/{file_id}/filename": "in.jpg",
            }
        )

    # OK-cases for uploaded data
    if file_id in (4, 5, 6, 7):
        return jsonify(
            {
                f"mediafile/{file_id}/id": file_id,
                f"mediafile/{file_id}/filename": str(file_id),
            }
        )

    # invalid responses
    if file_id == 10:
        return jsonify([None])
    if file_id == 11:
        return "some text"
    if file_id == 12:
        return "An error", 500
    if file_id == 13:
        return []
    if file_id == 14:
        return jsonify({f"mediafile/{file_id}/id": file_id})

    # not found or no perms
    if file_id == 20:
        return jsonify({})
