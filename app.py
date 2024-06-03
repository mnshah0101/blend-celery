from tasks import flask_app, long_running_task, update_pinecone_index
from celery.result import AsyncResult  # -Line 2
from flask import request, jsonify
from flask_cors import CORS

CORS(flask_app)


@flask_app.post("/trigger_task")
def start_task() -> dict[str, object]:
    iterations = request.args.get('iterations')
    print(iterations)
    result = long_running_task.delay(int(iterations))  # -Line 3
    return {"result_id": result.id}


@flask_app.route('/taskStatus', methods=['GET'])
def get_task_status():

    task_id = request.args.get('task_id')

    task = update_pinecone_index.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            "state": task.state,
            "status": "Pending..."
        }
    elif task.state != 'FAILURE':
        response = {
            "state": task.state,
            "status": task.info.get('status', ''),
            "result": task.info
        }
    else:
        response = {
            "state": task.state,
            "status": str(task.info)  # this is the exception raised
        }
    return jsonify(response)


@flask_app.get("/update_pinecone_index")
def handle_update():
    try:
        task = update_pinecone_index.apply_async()
        return jsonify({"status": "success", "result_id": task.id}), 202
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    flask_app.run(port=5000, debug=True)
