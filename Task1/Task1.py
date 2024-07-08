import os
import requests
import psycopg2
import webbrowser
import msal
import json

SCOPES = ['User.Read', 'Mail.Read', 'Mail.Send']
APP_ID = 'a7c0a132-7332-4d7e-a59b-879f4d227bcb'


def generate_access_token(app_id, scopes):
    access_token_cache = msal.SerializableTokenCache()
    if os.path.exists('api_token_access_arp.json'):
        access_token_cache.deserialize(open('api_token_access_arp.json', 'r').read())

    client = msal.PublicClientApplication(client_id=app_id, token_cache=access_token_cache)

    accounts = client.get_accounts()
    if accounts:
        token_response = client.acquire_token_silent(scopes, account=accounts[0])
    else:
        flow = client.initiate_device_flow(scopes=scopes)
        print('User code: ' + flow['user_code'])
        webbrowser.open(flow['verification_uri'])
        token_response = client.acquire_token_by_device_flow(flow)

    with open('api_token_access_arp.json', 'w') as _f:
        _f.write(access_token_cache.serialize())
    return token_response


def get_emails(access_token):
    endpoint = "https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime lt 2024-07-02T14:30:00Z"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    emails = []
    while endpoint:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            data = response.json()
            emails.extend(data.get('value', []))
            endpoint = data.get('@odata.nextLink')  # Get the nextLink if present
        else:
            raise Exception(f"Error fetching emails: {response.status_code} - {response.text}")
    return emails


def post_upload_emails(access_token):
    emails = get_emails(access_token)
    lst_of_all_sender_mails = []
    for set_of_from_mails in emails:
        try:
            sender_mail_id = set_of_from_mails['sender']['emailAddress']['address']
            lst_of_all_sender_mails.append(sender_mail_id)
        except KeyError:
            pass  # Handle the case where the key does not exist


    lst_of_unique_sender_mails = set(lst_of_all_sender_mails)

    payload = {
        "emailList": [{"0": email} for email in lst_of_unique_sender_mails]
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post("https://staging.jsjdmedia.com/api/get-filter", json=payload, headers=headers)
    if response.status_code == 200:
        print("POST request was successful.")
        print("Response:", json.dumps(response.json(), indent=4))
    else:
        print(f"POST request failed with status code {response.status_code}.")
        print("Response:", response.text)

    return len(lst_of_unique_sender_mails)


def main():
    token_response = generate_access_token(APP_ID, SCOPES)
    access_token = token_response['access_token']

    # Get emails and post them
    unique_email_count = post_upload_emails(access_token)
    print(f"Number of unique sender emails: {unique_email_count}")


if __name__ == "__main__":
    main()
