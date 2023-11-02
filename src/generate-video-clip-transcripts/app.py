import boto3
import os
import json
import uuid


VIDEO_PROCESSING_STAGING_PREFIX = os.environ.get('VIDEO_PROCESSING_STAGING_PREFIX')

transcribe = boto3.client('transcribe')

def lambda_handler(event, context):

    print(event)


    try:
        
        # Generate transcripts
        segments_json = generate_transcripts(event)

    except Exception:
        print("Error in generating transcripts")
        raise
     
    return segments_json
    
def generate_transcripts(segments_json):
    
    #Fetch video details
    video_bucket = segments_json['BatchInput']['Video']['S3Object']['Bucket']
    video_file_key = segments_json['BatchInput']['Video']['S3Object']['Name']
    video_file = video_file_key.split('/')[1]
    video_name = video_file.split('.')[0]

    segments = segments_json['Items']
    
    batch_index = 0

    try:
        # Start transcription job for each video clip
        for segment in segments:
            
            # Don't start job if clip doesn't have audio and video
            if segment['AudioOrVideoExists'] == 'No':
                batch_index = batch_index + 1
                continue
                
            job_name = f"GenerateVideoClipTranscript-{uuid.uuid4()}"
            
            #Fetch video clip name
            index = segment['ShotSegment']['Index']
            clip_name = f'{index}.mp4'   
            transcript_name = f'{index}.json'   
            
            video_file_uri = f"s3://{video_bucket}/{VIDEO_PROCESSING_STAGING_PREFIX}/{video_name}/{index}.mp4"
            transcript_file_key = f"{VIDEO_PROCESSING_STAGING_PREFIX}/{video_name}/{transcript_name}"
            
            response = transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={
                    'MediaFileUri': video_file_uri
                },
                MediaFormat="mp4",
                LanguageCode='en-US',
                OutputBucketName=video_bucket,
                OutputKey=transcript_file_key
                
            )   


            print(f"Started transcription job for {video_name}/{index}.mp4: {job_name}")
            
            segments_json['Items'][batch_index]['TranscriptionJobName'] = response['TranscriptionJob']['TranscriptionJobName']
            segments_json['Items'][batch_index]['TranscriptionJobStatus'] = response['TranscriptionJob']['TranscriptionJobStatus']
            
            batch_index = batch_index + 1
            
        
        return segments_json
        
    except Exception:
        raise        
        