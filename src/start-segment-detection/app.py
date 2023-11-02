# Write a python based Lambda function to invoke Amazon Rekognition Segments API to start segment detection job. Lambda gets triggered when copying .mp4 file to S3. Add error handling.
import boto3
import os

rekognition = boto3.client('rekognition')

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
REKOGNITION_ROLE_ARN = os.environ.get('REKOGNITION_ROLE_ARN')

def lambda_handler(event, context):
    try:
        
        print(event)

        bucket = event['Records'][0]['s3']['bucket']['name']
        
        key = event['Records'][0]['s3']['object']['key']
        
        
        # Call the Amazon Rekognition Video Segment Detection API
        response = rekognition.start_segment_detection(
            
            Video={'S3Object': {'Bucket': bucket, 'Name': key}},
            SegmentTypes=["SHOT"],
            NotificationChannel={
                'SNSTopicArn': SNS_TOPIC_ARN,
                'RoleArn': REKOGNITION_ROLE_ARN
            }
        
        )
        print(f"Starting segment detection job: {response}")

        return response
    except Exception as e:
        print(f"Error in segment detection job: {str(e)}")
        

