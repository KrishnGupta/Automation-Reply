import json
import msal
import requests
import webbrowser
import os
import boto3
import logging
import pandas as pd
import mysql.connector
from mysql.connector import Error, IntegrityError
from sqlalchemy import create_engine
from bs4 import BeautifulSoup
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants for OAuth2.0 authentication and API access
SCOPES = ['User.Read','Mail.Read']
APP_ID = 'a7c0a132-7332-4d7e-a59b-879f4d227bcb'
#
base_tmp_path = "/tmp/"

# Get current UTC time
current_utc_time = datetime.utcnow()
# Format to ISO 8601 string
formatted_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')


def generate_access_token(app_id, scopes):
    # Initialize the token cache
    access_token_cache = msal.SerializableTokenCache()
    local_filename_initial = 'api_token_access.json'
    filename = 'api_token_access_intermidiate.json'
    local_file_path = f'{base_tmp_path}{filename}'
    # Load token cache from file if it exists
    if os.path.exists(local_filename_initial):
        access_token_cache.deserialize(open(local_filename_initial, 'r').read())

    # Create MSAL public client application
    client = msal.PublicClientApplication(client_id=app_id, token_cache=access_token_cache)
    accounts = client.get_accounts()

    # Try to acquire token silently
    if accounts:
        token_response = client.acquire_token_silent(scopes, account=accounts[0])
    else:
        # Initiate device flow if no accounts are found
        flow = client.initiate_device_flow(scopes=scopes)
        print('User code :' + flow['user_code'])
        webbrowser.open(flow['verification_uri'])
        token_response = client.acquire_token_by_device_flow(flow)
    # Save the updated token cache to a file
    with open(local_file_path, 'w') as _f:
        _f.write(access_token_cache.serialize())
    return token_response


# Function to get unread emails
def get_emails(access_token):
    endpoint = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=isRead eq false&$top=500"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        emails = response.json()
        return emails.get('value', [])
    else:
        raise Exception(f"Error fetching emails: {response.status_code} - {response.text}")
         
# Function to convert HTML to plain text
def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def process_emails(email, filter_id,filter_name,filter_is_active,cursor,connection):
    data = []
    # for email in emails:
    subject = email['subject']
    sender_address = email['sender']['emailAddress']['address']
    full_body_html = email['body']['content']
    email_body_plain = html_to_text(full_body_html)
    # Check if the email matches the filter criteria
    if filter_name in subject or filter_name in email_body_plain:
        # email_body = email['bodyPreview']
        changeKey = email['changeKey']
        received_info = email['receivedDateTime']
        send_info = email['sentDateTime']
        try:
            sql = f"""INSERT INTO filters_mail_data (filterTableId,mailTo,sentTime,receiveTime,changeKey,subject,mailBody,mail_status,error_code, created_at, updated_at)
            values ({filter_id},'{sender_address}','{send_info}','{received_info}','{changeKey}','{subject}','{email_body_plain}',{filter_is_active},1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""    
            # cursor = connection.cursor()
            cursor.execute(sql)
            connection.commit()
            print("Record inserted successfully")

        except IntegrityError as e:
            # Handle duplicate key error
            if e.errno == 1062:  # 1062 is the error code for duplicate entry
                print(f"Duplicate entry for changeKey: {changeKey}. Record not inserted.")
            else:
                # Handle other IntegrityError exceptions
                print(f"IntegrityError: {e}")
    # connection.close()
    return 


# Function to post response data
def post_queries_to_api(access_token,json_data):
    # Define the API endpoint and headers for the POST request
    api_url = 'https://staging.jsjdmedia.com/api/get-filter'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    try:
        # Send the POST request with the JSON data and headers
        response = requests.post(api_url, headers=headers, json=json_data)
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        print('Data successfully sent to API.')
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            response_data = response.json()
            print("Response JSON:", json.dumps(response_data, indent=4))
        return response_data
    except requests.exceptions.HTTPError as err:
        # Handle HTTP errors
        print(f'HTTP error occurred: {err}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'HTTP error occurred: {err}')
        }
    except Exception as e:
        # Handle other exceptions
        print(f'Other error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Other error occurred: {e}')
        }

# Lambda function handler
def lambda_handler(event, context):
    HOST = "34.235.162.214"
    PORT = 3306
    USER = "staging_adbutler"
    PASSWORD = "staging_adbutler"
    DB = "staging_adbutler"
    TABLE_NAME = "automated_replies_filters"
    connection = mysql.connector.connect(host=HOST, port=PORT,user=USER,passwd=PASSWORD, db=DB)
    cursor = connection.cursor()
    # Connect to the database
    try:
        engine = create_engine(f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")
        logging.info("Database connection established")
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to connect to the database')
        }
    # Generate access token for Microsoft Graph API
    token_response = generate_access_token(APP_ID, SCOPES)
    access_token = token_response['access_token']
    emails = get_emails(access_token)

    # Use a set comprehension to gather unique email addresses
    email_address_set = {email.get('from', {}).get('emailAddress', {}).get('address')
        for email in emails if email.get('from', {}).get('emailAddress', {}).get('address')}
        
    # Create the dictionary in one step using list comprehension
    email_dict = {"emailList": [{str(1): email} for i, email in enumerate(email_address_set)]}
    print(f"email_dict----------{email_dict}")
    filter_data = post_queries_to_api(access_token,email_dict)
    filtered_data = []
    # Process input data
    for item in filter_data:
        # Check if filterData exists in the current item
        if "filterData" in item:
            filtered_data.append(item)    
    for email in emails:
        try:
            email_address = email['from']['emailAddress']['address']
            for filter in filtered_data:
                if filter['1'] == email_address:
                    for filter_item in filter['filterData']:
                        filter_info = filter_item['filterInfo']
                        filter_id = filter_info['id']
                        filter_name = filter_info['filterName']
                        filter_is_active = filter_info['is_active']
                        process_emails(email, filter_id,filter_name,filter_is_active,cursor,connection)
        except Exception as e:
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully inserted data in DB')
    }