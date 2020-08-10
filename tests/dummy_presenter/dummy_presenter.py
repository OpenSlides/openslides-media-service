from flask import Flask, request

app = Flask(__name__)

app.logger.info("Started Dummy-Presenter")


# for testing
@app.route("/system/presenter", methods=["POST"])
def dummy_presenter():
    app.logger.debug(f"dummy_presenter gets: {request.json}")
    meeting_id = request.json[0]["data"]["meeting_id"]
    return f"[{meeting_id}]"
