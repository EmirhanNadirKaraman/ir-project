import os
import youtube_transcript_api

# !pip install google-api-python-client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def youtube_authenticate():
    api_service_name = "youtube"
    api_version = "v3"
    developer_key = os.getenv("YOUTUBE_API_KEY")

    youtube = build(api_service_name, api_version, developerKey=developer_key)

    return youtube


def main():
    print("main called")
    youtube = youtube_authenticate()


if __name__ == '__main__':
    main()



