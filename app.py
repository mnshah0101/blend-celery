from tasks import process_campaign_task, process_video_task
from celery.result import AsyncResult 
from flask import request, jsonify
from flask_cors import CORS

from flask import Flask

flask_app = Flask(__name__)



CORS(flask_app)

@flask_app.route('/process_campaign', methods=['POST'])
def process_campaign():

    if 'campaign_id' not in request.json:
        return jsonify({'error': 'campaign_id is required'}), 400


    campaign_id = request.json['campaign_id']
    if not campaign_id:
        return jsonify({'error': 'campaign_id is required'}), 400


    task = process_campaign_task.delay(campaign_id)
    return jsonify({'task_id': task.id})

@flask_app.route('/process_video', methods=['POST'])
def process_video():
    if 'video_id' not in request.json:
        return jsonify({'error': 'video_id is required'}), 400
    video_id = request.json['video_id']

    if not video_id:
        return jsonify({'error': 'video_id is required'}), 400

    task = process_video_task.delay(video_id)
    return jsonify({'task_id': task.id})

#endpoint to get the status of a task


@flask_app.get("/task_status")
def task_result() -> dict[str, object]:
    result_id = request.args.get('task_id')
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



if __name__ == "__main__":
    flask_app.run(port=3001, debug=True)
