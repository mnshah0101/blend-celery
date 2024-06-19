from config import create_app  # -Line 1
from celery import shared_task
import os

from werkzeug.utils import secure_filename
from utils.s3 import upload_file_to_s3
from utils.llm import create_script
from utils.mongoUser import create_user_in_mongo, validate_user
from utils.mongoCampaign import createCampaign, update_campaign, get_campaigns_by_status, get_campaigns_by_user_id, get_campaign_by_id
from utils.mongoVideo import create_video, update_video, get_videos_by_campaign_id_and_status, get_videos_by_status, get_videos_by_campaign_id, get_video_by_id
from utils.videoProcessing import extract_audio_from_s3_video_and_upload
from utils.transcribe import transcribe_audio_from_url
from utils.elevenLabs import create_voice, create_audio_from_script
from utils.synclabs import create_video_from_audio, get_synclabs_video_from_id
import dotenv

dotenv.load_dotenv()

S3_VIDEO_BUCKET = os.getenv('S3_VIDEO_BUCKET')
S3_AUDIO_BUCKET = os.getenv('S3_AUDIO_BUCKET')

flask_app = create_app()  # -Line 2
celery_app = flask_app.extensions["celery"]  # -Line 3


@shared_task(ignore_result=False)
def process_campaign_task(campaign_id):
    campaign = get_campaign_by_id(campaign_id)

    if 'status' not in campaign:
        return {'error': 'Campaign does not exist'}

    if campaign['status'] != 'object_created':
        return {'error': 'Campaign is not in object_created status'}

    # Extract audio from video
    audio_s3_url = extract_audio_from_s3_video_and_upload(
        campaign['video_url'], f'campaign_video.mp4', 'campaign_audio.mp3', S3_AUDIO_BUCKET, 'campaigns/' + campaign_id + ".mp3")
    update_campaign({'audio_url': audio_s3_url}, campaign_id)
    update_campaign({'status': 'audio_extracted'}, campaign_id)

    # Transcribe audio
    transcript = transcribe_audio_from_url(audio_s3_url)
    update_campaign({'script': transcript}, campaign_id)
    update_campaign({'status': 'audio_transcribed'}, campaign_id)

    # Create voice
    response = create_voice(campaign['sample'], campaign['name'])
    update_campaign(
        {'eleven_labs_voice_id': response['voice_id']}, campaign_id)
    update_campaign({'status': 'voice_created'}, campaign_id)


@shared_task(ignore_result=False)
def process_video_task(video_id):
    video = get_video_by_id(video_id)
    if 'campaign_id' not in video:
        return {'error': 'Video does not exist'}

    if video['status'] != 'object_created':
        return  {'error': 'Video is not in object_created status'}

    campaign = get_campaign_by_id(video['campaign_id'])

    if 'status' not in campaign:
        return {'error': 'Campaign does not exist'}

    if campaign['status'] != 'voice_created':
        return {'error': 'Campaign is not in voice_created status'}

    # Create script
    new_script = create_script(campaign['script'], str(video['data']))
    update_video({'script': new_script}, video_id)

    # Create audio from script
    audio_url = create_audio_from_script(
        campaign['eleven_labs_voice_id'], new_script, video_id)
    update_video({'audio_url': audio_url}, video_id)
    update_video({'status': 'audio_created'}, video_id)

    # Create video from audio
    response = create_video_from_audio(
        audio_url, campaign['video_url'])
    update_video({'video_url': response['url']}, video_id)
    update_video({'sync_labs_id': response['id']}, video_id)
    update_video({'status': 'video_creating'}, video_id)
