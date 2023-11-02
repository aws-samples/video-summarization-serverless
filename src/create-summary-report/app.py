import boto3
import os
import json
from fpdf import FPDF
import botocore


VIDEO_SUMMARY_FILES_PREFIX = os.environ.get('VIDEO_SUMMARY_FILES_PREFIX')
VIDEO_PDF_REPORT_FILES_PREFIX = os.environ.get('VIDEO_PDF_REPORT_FILES_PREFIX')
PRESIGNED_URL_EXPIRATION = os.environ.get('PRESIGNED_URL_EXPIRATION')
VIDEO_SUMMARY_TABLE = os.environ.get('VIDEO_SUMMARY_TABLE')

s3 = boto3.client('s3')
ddb = boto3.resource("dynamodb").Table(VIDEO_SUMMARY_TABLE)
pdf = FPDF()

def lambda_handler(event, context):

    print(event)


    try:
        
        # Create PDF report
        segments_json = create_pdf_report(event)

    except Exception:
        print("Error in creating summary report")
        raise
     
    return segments_json

def create_pdf_report(segments_json):
    
    #Fetch video details
    video_bucket = segments_json['Video']['S3Object']['Bucket']
    video_file_key = segments_json['Video']['S3Object']['Name']
    video_file = video_file_key.split('/')[1]
    video_name = video_file.split('.')[0]
    
    tmp_pdf_file_path = f"/tmp/{video_name}.pdf"
    s3_pdf_file = f'{VIDEO_PDF_REPORT_FILES_PREFIX}/{video_name}.pdf'
    
    print(f"Starting summary report generation process")
    
    # Create PDF 
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    segments = segments_json['Segments']
    
    print(segments)
    
    try:
        for segment in segments:
            
            print(f"Fetching report files for: {segment}")

            #Fetch summary and thumbnail file name for each segment
            index = segment['ShotSegment']['Index']
            summary_file = f'{index}.txt'
            thumbnail_file = f'{index}.jpg'
            
            try:
                # Download files
                s3.download_file(video_bucket, f'{VIDEO_SUMMARY_FILES_PREFIX}/{video_name}/{thumbnail_file}',f'/tmp/{thumbnail_file}')
                s3.download_file(video_bucket, f'{VIDEO_SUMMARY_FILES_PREFIX}/{video_name}/{summary_file}',f'/tmp/{summary_file}')
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    # If the file doesn't exist, continue to the next file
                    print(f"File for segment {index} not found. Skipping")
                    continue
                else:
                    print(f"Error downloading file for segment {index}: {str(e)}")
                    

            
            # Add image to the PDF
            pdf.image(f'/tmp/{thumbnail_file}', x=10, w=190)
            
            # Add the txt from .txt file
            with open(f'/tmp/{summary_file}', 'r') as txt_file:
                text_content = txt_file.read()
                pdf.multi_cell(0,10,text_content)
         
            pdf.ln(10)
            
            # Clean up temporary files
            os.remove(f'/tmp/{thumbnail_file}')
            os.remove(f'/tmp/{summary_file}')
            

        # Save the pdf 
        pdf.output(tmp_pdf_file_path)
        
        # Upload the PDF to an output S3 bucket
        s3.upload_file(tmp_pdf_file_path, video_bucket, s3_pdf_file)
        
        #create pre-signed url
        url = s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': video_bucket,
                    'Key': s3_pdf_file,
                },
                ExpiresIn=PRESIGNED_URL_EXPIRATION
        )
        
        os.remove(tmp_pdf_file_path)
        
        segments_json['ReportFile'] = url
        
        ddb_item = {
            "fileName": video_file.strip(),
            "pre-signedURL": url
        }
        
        print(ddb_item)
        
        ddb.put_item(Item=ddb_item)
        
        return segments_json
        
    except Exception:
        
        if os.path.exists(tmp_pdf_file_path):
            os.remove(tmp_pdf_file_path)
        raise        
        