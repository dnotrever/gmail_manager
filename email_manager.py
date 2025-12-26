import base64
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from blacklist import black_list

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


#=============================================================================================================
# Gmail Authentication
#=============================================================================================================

def authenticate_gmail():

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


#=============================================================================================================
# Gmail Email Management
#=============================================================================================================

def get_header(email, header_name):

    headers = email.get('payload', {}).get('headers', [])

    for header in headers:
        if header['name'] == header_name:
            return header['value']
        
    return None

def find_body(payload, prefer_html=True):

    mime = payload.get('mimeType', '')
    body = payload.get('body', {})

    if mime == 'text/html' and body.get('data'):
        return base64.urlsafe_b64decode(body['data']).decode('utf-8', errors='ignore')

    if mime == 'text/plain' and body.get('data') and not prefer_html:
        return base64.urlsafe_b64decode(body['data']).decode('utf-8', errors='ignore')

    for part in payload.get('parts', []):
        result = find_body(part, prefer_html)
        if result:
            return result

    return None

def get_email_body(email):

    payload = email.get('payload', {})

    body = find_body(payload, prefer_html=True)

    if not body:
        body = find_body(payload, prefer_html=False)

    return body or 'No content.'

def list_messages(service, max_results=50):

    results = service.users().messages().list(
        userId='me',
        maxResults=max_results
    ).execute()

    messages = []

    for msg in results.get('messages', []):

        full = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        email_data = {
            'id': full.get('id'),
            'from': get_header(full, 'From'),
            'subject': get_header(full, 'Subject'),
            'date': get_header(full, 'Date'),
            'body': get_email_body(full),
            'snippet': full.get('snippet'),
            'labels': full.get('labelIds', []),
        }

        messages.append(email_data)

    return messages

def delete_email(service, message):

    print('')

    infos = f"{message['id']} | {message['from']} | {message['subject']}"

    try:
        service.users().messages().trash(userId='me', id=message['id']).execute()
        print(f"Deleted email: {infos}")
    except Exception as err:
        print(f"Failed to delete email: {infos}")
        print(err)

def delete_blacklisted_emails(service):

    messages = list_messages(service)

    for msg in messages:

        _subject = msg['subject'] or ''
        _from = msg['from'] or ''

        if any(black_item in _subject for black_item in black_list) or any(black_item in _from for black_item in black_list):
            delete_email(service, msg)
            

#=============================================================================================================
# Main Execution
#=============================================================================================================

if __name__ == '__main__':

    service = authenticate_gmail()

    # results = list_messages(service, max_results=5)

    # for msg in results:
    #     print(f"{msg['id']} | {msg['from']} | {msg['subject']}")

    delete_blacklisted_emails(service)

    print('')

