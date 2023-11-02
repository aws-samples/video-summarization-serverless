# Write a python based Lambda function to invoke Amazon Rekognition Segments API to start segment detection job. Lambda gets triggered when copying .mp4 file to S3. Add error handling.
import boto3
import os

step_function = boto3.client("stepfunctions")

STATE_MACHINE_VIDEO_PROCESSING_ARN = os.environ.get('STATE_MACHINE_VIDEO_PROCESSING_ARN')

def lambda_handler(event, context):
    try:
        
        print('Starting video processing workflow')    
        sns_message = event['Records'][0]['Sns']['Message']
        print(sns_message)
        
        
        step_function.start_execution(
            
            stateMachineArn=STATE_MACHINE_VIDEO_PROCESSING_ARN,
            input=sns_message,

        )
        
        return True
        
    except Exception as e:
        print(f"Error in starting workflow: {str(e)}")
        

