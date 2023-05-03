import json
import os

# !pip install google-api-python-client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

import scrapetube

def youtube_authenticate():
    api_service_name = "youtube"
    api_version = "v3"
    developer_key = os.getenv("YOUTUBE_API_KEY")

    youtube = build(api_service_name, api_version, developerKey=developer_key)

    return youtube


def main():
    print("main called")
    youtube = youtube_authenticate()

    channels = json.loads(open('channels.json').read())

    for channel in channels:
        videos = scrapetube.get_channel(channel['id'])

        for video_id in videos:
            response = youtube.videos().list(
                part="snippet",
                id=video_id
            ).execute()

            print(response)
            break






if __name__ == '__main__':
    main()



