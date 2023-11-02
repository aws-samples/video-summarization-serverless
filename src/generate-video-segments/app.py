import boto3
import os
import json
import subprocess
import shlex


VIDEO_PROCESSING_STAGING_PREFIX = os.environ.get('VIDEO_PROCESSING_STAGING_PREFIX')
VIDEO_SUMMARY_FILES_PREFIX = os.environ.get('VIDEO_SUMMARY_FILES_PREFIX')

s3_client = boto3.client('s3')

def lambda_handler(event, context):

    print(event)


    try:
        
        # Generate clips
        segments_json = create_segment_files(event)

    except Exception:
        print("Error in parsing segments")
        raise
     
    return segments_json

def create_segment_files(segments_json):
    
    #Fetch video details
    video_bucket = segments_json['BatchInput']['Video']['S3Object']['Bucket']
    video_file_key = segments_json['BatchInput']['Video']['S3Object']['Name']
    video_file = video_file_key.split('/')[1]
    video_name = video_file.split('.')[0]
    
    print(f"Starting segementaton process for {video_bucket}/{video_file_key}")

    tmp_video_path = f'/tmp/{video_file}'

    s3_client.download_file(video_bucket, video_file_key, tmp_video_path)    
    
    segments = segments_json['Items']
    
    batch_index = 0
    
    print(segments)
    try:
        for segment in segments:
            
            print(f"Creating video clip for: {segment}")
            start_time = segment['StartTimestampMillis'] / 1000.0
            duration = segment['DurationMillis'] / 1000.0
            
            #Create clip name and thumbnail name using the index of each segment
            index = segment['ShotSegment']['Index']
            clip_name = f'{index}.mp4'
            thumbnail_name = f'{index}.jpg'
            
            # Use ffmpeg to split the video into a clip
            subprocess.run([
                '/opt/bin/ffmpeg',
                '-i', shlex.quote(tmp_video_path),
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', 'copy',
                '-c:a', 'copy',
                f'/tmp/{shlex.quote(clip_name)}'
            ], check=True)
            
            # Upload the clip to the destination S3 bucket
            s3_client.upload_file(f'/tmp/{clip_name}', video_bucket, f'{VIDEO_PROCESSING_STAGING_PREFIX}/{video_name}/{clip_name}')
            
            # Check if the generated clip has video and audio streams
            ffprobe_command = [
                '/opt/bin/ffprobe',
                '-i', f'/tmp/{shlex.quote(clip_name)}',
                '-show_streams'
            ]
            stream_info = subprocess.check_output(ffprobe_command, stderr=subprocess.STDOUT).decode()
                
            # if video and audio stream exist, create thumbnail    
            if "video" in stream_info and "audio" in stream_info:
                
                subprocess.run([
                    '/opt/bin/ffmpeg',
                    '-i', f'/tmp/{shlex.quote(clip_name)}',
                    '-vf', 'thumbnail',
                    '-frames:v', '1',
                    f'/tmp/{shlex.quote(thumbnail_name)}'
                ], check=True)
                
                 # Upload the clip to the destination S3 bucket
                s3_client.upload_file(f'/tmp/{thumbnail_name}', video_bucket, f'{VIDEO_SUMMARY_FILES_PREFIX}/{video_name}/{thumbnail_name}')
                os.remove(f'/tmp/{thumbnail_name}')
                segments_json['Items'][batch_index]['AudioOrVideoExists'] = 'Yes'
            
            else:
                segments_json['Items'][batch_index]['AudioOrVideoExists'] = 'No'
    
            os.remove(f'/tmp/{clip_name}')
            
            batch_index = batch_index + 1
            
    
        os.remove(tmp_video_path)
        
        return segments_json
        
    except Exception:
        
        if os.path.exists(tmp_video_path):
            os.remove(tmp_video_path)
        raise        

