import boto3
import json

transcribe = boto3.client('transcribe')

def lambda_handler(event, context):

    print(event)


    try:
        
        segments_json = event
        segments = segments_json['Items']
        batch_index = 0
        
        # For each segment, check job status. Return immediately if any queued or in-progress segment found
        for segment in segments:
            
            # Transcription jobs are not available for the clip with no audio and video
            if segment['AudioOrVideoExists'] == 'No':
                batch_index = batch_index + 1
                continue
            
            job_name = segment['TranscriptionJobName']
            job_status = segment['TranscriptionJobStatus']
            
            # Call get_transcription_job only if job status is IN_PROGRESS or QUEUED
            if job_status in ['IN_PROGRESS', 'QUEUED']:

                response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
                job_status = response['TranscriptionJob']['TranscriptionJobStatus']
                segments_json['Items'][batch_index]['TranscriptionJobStatus'] = job_status
                
                if job_status in ['IN_PROGRESS', 'QUEUED']:
                    segments_json['AllJobStatus'] = 'IN_PROGRESS'
                    return segments_json
            
            
            batch_index = batch_index + 1
        
        segments_json['AllJobStatus'] = 'COMPLETED'
        
        return segments_json

    except Exception:
        print("Error in checking job status")
        raise
     
    
    
