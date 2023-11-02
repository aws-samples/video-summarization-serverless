import boto3
import os
import json
import uuid


VIDEO_PROCESSING_STAGING_PREFIX = os.environ.get('VIDEO_PROCESSING_STAGING_PREFIX')
VIDEO_SUMMARY_FILES_PREFIX = os.environ.get('VIDEO_SUMMARY_FILES_PREFIX')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID')
REGION = os.environ.get('AWS_REGION')

s3 = boto3.client('s3')
bedrock = boto3.client(service_name='bedrock-runtime', region_name=REGION)


def lambda_handler(event, context):

    print(event)


    try:
        
        # Summarize transcripts
        summarize_transcripts(event)

    except Exception:
        print("Error in summarizing transcripts")
        raise
    

        

def invoke_endpoint(json):
    print(f"Request: {json}")
    response = bedrock.invoke_model(body=json, modelId=BEDROCK_MODEL_ID, accept='application/json', contentType='application/json')
    return response


def parse_response(response):
    responce_body = json.loads(response.get('body').read())
    print(f"Response body: {responce_body}")
    generated_text = responce_body['completions'][0]['data']['text']
    return generated_text        
    
def summarize_transcripts(segments_json):
    
    #Fetch video details
    video_bucket = segments_json['BatchInput']['Video']['S3Object']['Bucket']
    video_file_key = segments_json['BatchInput']['Video']['S3Object']['Name']
    video_file = video_file_key.split('/')[1]
    video_name = video_file.split('.')[0]

    #Summarize only those segments with audio and video
    segments_with_av = filter(lambda item: item.get('AudioOrVideoExists') == 'Yes', segments_json['Items'])
    
    try:
        # Start transcription job for each video clip
        for segment in segments_with_av:
            
            print(f"Summarizing video clip: {segment}")
            #Fetch transcript file name
            index = segment['ShotSegment']['Index']
            transcript_file_name = f'{index}.json' 
            summary_file_name = f'{index}.txt'
        
            transcript_file_key =f"{VIDEO_PROCESSING_STAGING_PREFIX}/{video_name}/{transcript_file_name}"

            transcript_response = s3.get_object(Bucket=video_bucket, Key=transcript_file_key)
            transcript_data = transcript_response['Body'].read().decode('utf-8')
        
            # Parse the JSON data  
            transcript_json = json.loads(transcript_data)
            transcript = transcript_json['results']['transcripts'][0]['transcript']
            
            # Summarize video transcript
            # Invokde Bedrock API to summarize transcript
            instruction = 'Summarize the context above.'
            text_input = '{}\n\n{}'.format(transcript, instruction)
            payload = {
                "prompt": text_input,
                "maxTokens": 500,
                "temperature": 0.5,
                "topP": 0.5,
                "stopSequences": [],
                "countPenalty": {"scale": 0 }, 
                "presencePenalty": {"scale": 0 }, 
                "frequencyPenalty": {"scale": 0 }
            }
            response = invoke_endpoint(json.dumps(payload))
            
            summary = parse_response(response)     
            
            response = s3.put_object(Body=summary, Bucket=video_bucket, Key=f'{VIDEO_SUMMARY_FILES_PREFIX}/{video_name}/{summary_file_name}')
        
            
    except Exception:
        raise    


    