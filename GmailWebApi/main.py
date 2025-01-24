import os

from gmail_client import GmailClient


def get_txt_files(directory):
    txt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt"):
                txt_files.append(os.path.join(root, file))
    return txt_files


for cookies_file in reversed(get_txt_files(r'C:\Users\Admin\Desktop\Gmail Cookies')):
    cookies_file = 'C:\\Users\\Admin\\Desktop\\Gmail Cookies\\[0] [yepyaeko308989@gmail.com].txt'
    client = GmailClient(cookies_file=str(cookies_file))
    sessions = client.get_sessions()

    for session in sessions:
        if session.email not in cookies_file:
            continue
        # if '308989' not in session.email:
        #     continue
        # print(f"Valid session!\n"
        #       f"Name: {session.name}\n"
        #       f"Email: {session.email}\n"
        #       f"Avatar: {session.avatar}\n"
        #       f"Index (u): {session.index}\n"
        #       f"AccountId: {session.account_id}"
        #       )

        params = {
            'sw': '2',
        }
        email_code_response = client.session.get(f'https://mail.google.com/mail/u/{session.index}/')
        email_code = email_code_response.text.split('\"\\\\u003e\\\\r\\\\n\\\\t\\\\t\\\\t\\\\t\\\\t\\\\t\\\\u003cp\\\\u003e\\\\u003cb\\\\u003e')[-1].split('\\')[0]

