from tasks import flask_app, long_running_task, update_pinecone_index
from celery.result import AsyncResult  # -Line 2
from flask import request, jsonify


@flask_app.post("/trigger_task")
def start_task() -> dict[str, object]:
    iterations = request.args.get('iterations')
    print(iterations)
    result = long_running_task.delay(int(iterations))  # -Line 3
    return {"result_id": result.id}


@flask_app.get("/get_result")
def task_result() -> dict[str, object]:
    result_id = request.args.get('result_id')
    result = AsyncResult(result_id)  # -Line 4
    if result.ready():  # -Line 5
        # Task has completed
        if result.successful():  # -Line 6

            return {
                "ready": result.ready(),
                "successful": result.successful(),
                "value": result.result,  # -Line 7
            }
        else:
            # Task completed with an error
            return jsonify({'status': 'ERROR', 'error_message': str(result.result)})
    else:
        # Task is still pending
        return jsonify({'status': 'Running'})


@flask_app.get("/update_pinecone_index")
def handleUpdate():
    update_pinecone_index.delay()
    return "Pinecone index update triggered"


if __name__ == "__main__":
    flask_app.run(port=5000, debug=True)
