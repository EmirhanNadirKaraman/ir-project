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

from utils import *


class Channel:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.videos = scrapetube.get_channel(channel_id)
        self.subscriber_count = None


    def set_subscriber_count(self, count):
        self.subscriber_count = count



class Video:
    def __init__(self, video_json, response_json):
        self.video_json = video_json
        self.response_json = response_json
        self.stat_json = get_stat_from_response_json(self.response_json)

        self.title = self.get_video_title()
        self.description = self.get_video_description()
        self.view_count = get_view_count_from_video_json(self.video_json)

        self.duration = self.get_video_duration()
        self.publish_date = self.get_video_publish_date()
        self.thumbnails = self.get_video_thumbnails()

        self.video_id = self.video_json['videoId']
        self.channel_id = get_channel_id_from_response_json(self.response_json)


    def __str__(self):
        title = f'title: {self.title}'
        view_count = f'view_count: {self.view_count}'
        duration = f'duration: {self.duration}'
        publish_date = f'publish_date: {self.publish_date}'
        channel_id = f'channel_id: {self.channel_id}'

        return '\n'.join([title, view_count, duration, publish_date, channel_id])
    

    def get_video_title(self):
        return self.video_json['title']['runs'][0]['text']


    def get_video_description(self):
        return self.video_json['descriptionSnippet']['runs'][0]['text']
    

    def get_video_duration(self):
        return self.video_json['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']['text']['simpleText']


    def get_video_publish_date(self):
        return self.response_json['items'][0]['snippet']['publishedAt']


    def get_video_thumbnails(self):
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
        self.file_name = 'channels.json'
        self.channels = [Channel(channel['id']) for channel in json.loads(open(self.file_name).read())]


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
                    response_json = get_video_info(video_json=video_json)
                    results.update({
                        video_id: {
                            'video': video_json,
                            'response': response_json,
                            'stats': get_channel_stat_info(response_json)
                        }
                    })

                    """results.update({
                        video_id: {
                            'video': {
                                'title': video_json['title']['runs'][0]['text'],
                                'description': video_json['descriptionSnippet']['runs'][0]['text'],
                                'duration': video_json['thumbnailOverlays'][0]['thumbnailOverlayTimeStatusRenderer']
                                            ['text']['simpleText'],
                                'publish_date': response_json['items'][0]['snippet']['publishedAt'],
                                'thumbnails': [Thumbnail(url=element['url'],
                                                        width=element['width'],
                                                        height=element['height']) 
                                                        for element in response_json['items'][0]
                                                        ['snippet']['thumbnails']],
                                'video_id': video_json['videoId'],
                                'view_count': get_view_count_from_video_json(video_json)
                            },
                            'channel': {
                                'channel_id': response_json['items'][0]['snippet']['channelId'],
                                'channel_title': response_json['items'][0]['snippet']['channelTitle'],
                                'subscriber_count': get_subscriber_count_of_video_owner(channels=self.channels, 
                                                                                        video=video_json)
                            }
                        },
                    })"""

                video_json = results[video_id]['video']
                response_json = results[video_id]['response']
                 
                video = Video(video_json=video_json, response_json=response_json)
                channel = get_channel_of_video(channels=self.channels, video=video)

                channel.subscriber_count = get_subscriber_count_of_video_owner(channels=self.channels, video=video)

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
    
    
    def plot_results(self, max_days_old: int, channel_count: int, no_of_bins: int) -> None:
        videos = self.get_results(max_days_old=max_days_old, channel_count=channel_count)

        views = []
        channel_sub_counts = []

        with open('results.json', 'r') as f:
            results = json.loads(f.read())
            
        for video in videos: 
            result = results[video.video_id]

            view_count = get_view_count_from_video_json(result['video'])
            channel_sub_count = get_subscriber_count_from_json(result['stats'])

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
