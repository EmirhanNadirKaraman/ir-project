import json
import os
import scrapetube

import matplotlib.pyplot as plt

# pip install google-api-python-client
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
from config import set_values
from datetime import datetime, timezone
from math import tanh


class Channel:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.videos = scrapetube.get_channel(channel_id)
        self.subscriber_count = None


class Video:
    def __init__(self, video_json, response_json):
        self.video_json = video_json
        self.response_json = response_json

        self.title = self.get_title()
        self.description = self.get_description()
        self.view_count = self.get_view_count()

        self.duration = self.get_duration()
        self.publish_date = self.get_publish_date()
        self.thumbnails = self.get_thumbnails()

        self.video_id = self.video_json['videoId']
        self.channel_id = self.response_json['items'][0]['snippet']['channelId']


    def __str__(self):
        title = f'title: {self.title}'
        view_count = f'view_count: {self.view_count}'
        duration = f'duration: {self.duration}'
        publish_date = f'publish_date: {self.publish_date}'
        channel_id = f'channel_id: {self.channel_id}'

        return '\n'.join([title, view_count, duration, publish_date, channel_id])
    

    def get_max_res_thumbnail(self):
        max_res = self.thumbnails[0]
        for thumbnail in self.thumbnails:
            if thumbnail.width > max_res.width:
                max_res = thumbnail

        return max_res

    def get_title(self):
        return self.video_json['title']['runs'][0]['text']

    def get_description(self):
        return self.video_json['descriptionSnippet']['runs'][0]['text']

    def get_view_count(self):
        def convert_view_count(view_count: str) -> int:
            return int(view_count.replace('.', ''))

        temp_count = self.video_json['viewCountText']['simpleText'].split()[0]
        return convert_view_count(temp_count)

    def get_duration(self):
        return self.video_json['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['text']['simpleText']

    def get_publish_date(self):
        return self.response_json['items'][0]['snippet']['publishedAt']

    def get_thumbnails(self):
        thumbnails = []

        thumbnail_json = self.response_json['items'][0]['snippet']['thumbnails']

        for element in thumbnail_json:
            element = thumbnail_json[element]
            thumbnails.append(Thumbnail(url=element['url'],
                                        width=element['width'],
                                        height=element['height']))

        return thumbnails


class SubScraper:
    def __init__(self):
        set_values()
        self.developer_key = os.getenv('YOUTUBE_API_KEY')
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.youtube = self._authenticate()

        self.file_name = 'channels.json'
        self.channels = [Channel(channel['id']) for channel in json.loads(open(self.file_name).read())]


    def _authenticate(self):
        youtube = build(self.api_service_name,
                        self.api_version,
                        developerKey=self.developer_key)

        return youtube


    def get_video_info(self, video) -> str:
        info = self.youtube.videos().list(
            part="snippet",
            id=video['videoId']
        ).execute()

        return info


    def get_channel_stat_info(self, response_json: str) -> str:
        channel_id = response_json['items'][0]['snippet']['channelId']
    
        # if video is not processed before
        info = self.youtube.channels().list(
            part="statistics",
            id=channel_id
        ).execute()

        return info
    
    
    def get_subscriber_count(self, video: Video) -> int:
        def convert_view_count(view_count: str) -> int:
            return int(view_count.replace('.', ''))
        
        channel = self.get_channel(video)

        if channel.subscriber_count is not None:
            return channel.subscriber_count
        
        stat_json = self.get_channel_stat_info(video.response_json)
        sub_count_str = stat_json['items'][0]['statistics']['subscriberCount']

        channel.subscriber_count = convert_view_count(sub_count_str)

        return channel.subscriber_count


    def get_results(self, max_days_old: int, channel_count: int) -> list[Video]:
        videos = []

        # create results.json if it doesn't exist
        if not os.path.exists('results.json'):
            with open('results.json', 'w') as f:
                f.write('{}')

        with open('results.json', 'r') as f:
            results = json.loads(f.read())

        for channel_index, channel in enumerate(self.channels[:channel_count]):
            for video_index, video_json in enumerate(channel.videos):
                video_id = video_json['videoId']
                
                if video_id not in results:
                    response_json = self.get_video_info(video=video_json)
                    results.update({
                        video_id: {
                            'video': video_json,
                            'response': response_json,
                            'stats': self.get_channel_stat_info(response_json)
                        }
                    })

                video_json = results[video_id]['video']
                response_json = results[video_id]['response']
                 
                video = Video(video_json=video_json, response_json=response_json)
                channel = self.get_channel(video)
                channel.subscriber_count = self.get_subscriber_count(video)

                publish_date = datetime.fromisoformat(video.publish_date.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc).astimezone()

                days_old = (now - publish_date).days

                if days_old > max_days_old:
                    break

                videos.append(video)
                print(channel_index, video_index)

        with open('results.json', 'w') as f:
            json.dump(results, f, indent=4)

        return videos
    
    def get_channel(self, video: Video) -> Channel:
        for channel in self.channels:
            if channel.channel_id == video.channel_id:
                return channel
        
        # if channel does not exist, return None
        return None
    
    def plot_results(self, max_days_old: int, channel_count: int, no_of_bins: int) -> None:
        def convert_view_count(view_count: str) -> int:
            return int(view_count.replace('.', ''))
        
        videos = self.get_results(max_days_old=max_days_old, channel_count=channel_count)

        views = []
        channel_sub_counts = []

        with open('results.json', 'r') as f:
            results = json.loads(f.read())

        for video in videos: 
            result = results[video.video_id]
            view_count = convert_view_count(result['video']['viewCountText']['simpleText'].split()[0])
            channel_sub_count = int(result['stats']['items'][0]['statistics']['subscriberCount'])

            views.append(view_count)
            channel_sub_counts.append(channel_sub_count)

        subscriber_mean = sum(set(channel_sub_counts)) / len(channel_sub_counts)

        normalized_views = [view / self.normalize(sub_count, subscriber_mean) 
                            for view, sub_count in zip(views, channel_sub_counts)]

        plt.hist(normalized_views, bins=no_of_bins)
        plt.xlabel('views')
        plt.ylabel('frequency')
        plt.title(f'Views of videos from the last {max_days_old} days')
        plt.show()

    def normalize(self, subscriber_count, mean):
        # print(subscriber_count, tanh(subscriber_count))
        # print(mean, tanh(mean))
        return tanh(subscriber_count) / tanh(mean) * 0.5


class Thumbnail:
    def __init__(self, url, width, height):
        self.url = url
        self.width = width
        self.height = height

    def __str__(self):
        url = f'url: {self.url}'
        width = f'width: {self.width}'
        height = f'height: {self.height}'

        return '\n'.join([url, width, height])


def main():
    subscraper = SubScraper()
    subscraper.plot_results(max_days_old=40, channel_count=1, no_of_bins=1000)


if __name__ == '__main__':
    main()
