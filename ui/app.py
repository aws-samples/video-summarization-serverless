import streamlit as st
import boto3
import pandas as pd
from htmlTemplates import css, bot_template, user_template



ddb_client = boto3.resource("dynamodb").Table("VideoSummaryTable")

response = ddb_client.scan()
data = response['Items']

st.set_page_config(page_title="Video Summarization", page_icon=":books::parrot:")
st.write(css, unsafe_allow_html=True)
df=pd.DataFrame(data)





def make_clickable(link):
    # target _blank to open new window
    # extract clickable text to display for your link
    text = link.split('=')[1]
    return f'<a target="_blank" href="{link}">{text}</a>'
    
#df['pre-signedURL'] = df['pre-signedURL'].apply(make_clickable)

records = df.to_dict("records")

selected_data = st.selectbox('Please select video file:',options=records, format_func=lambda record: record['fileName'])

st.write('**Video File**:', selected_data['fileName'])  

pdf_filename = f"{selected_data['fileName'].split('.')[0]}.pdf"

st.write('**Download PDF File**:', f'<a target="_blank" href="{selected_data["pre-signedURL"]}">{pdf_filename}</a>',unsafe_allow_html=True)

