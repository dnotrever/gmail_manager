import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():

    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def get_header(email, header_name):

    headers = email.get('payload', {}).get('headers', [])

    for header in headers:
        if header['name'] == header_name:
            return header['value']
        
    return None

def get_email_body(email):

    parts = email.get('payload', {}).get('parts', [])

    for part in parts:
        if part.get('mimeType') == 'text/plain':
            return part.get('body', {}).get('data', '')
        
    return 'No content.'

def list_emails(service, max_results=10):

    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])

    print('\nEmails:')

    for msg in messages:
        message = service.users().messages().get(userId='me', id=msg['id']).execute()
        print(f"ID: {msg['id']} | Subject: {get_header(message, 'Subject')}")

    return messages

def get_email_details(service, email_id):

    email = service.users().messages().get(userId='me', id=email_id).execute()
    subject = get_header(email, 'Subject')
    sender = get_header(email, 'From')
    body = get_email_body(email)

    print(f"Subject: {subject}\nFrom: {sender}\nContent:\n{body}")

    return email

def delete_email(service, email_id):

    service.users().messages().delete(userId='me', id=email_id).execute()

    print(f"E-mail {email_id} apagado com sucesso!")


if __name__ == '__main__':

    service = authenticate_gmail()

    emails = list_emails(service)

    if emails:

        email_position = 5

        email_id = emails[email_position]['id']

        print(f"\nE-mail {email_position + 1} details:")

        get_email_details(service, email_id)

    print('')

