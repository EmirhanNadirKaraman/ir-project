import json
import os
import scrapetube

import matplotlib.pyplot as plt

# pip install google-api-python-client

from datetime import datetime, timezone
import math

from utils import *


class Channel:
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.videos = scrapetube.get_channel(channel_id)
        self.subscriber_count = None

    def set_subscriber_count(self, count):
        self.subscriber_count = count

    def __str__(self):
        return (
            f"channel_id: {self.channel_id}\nsubscriber_count: {self.subscriber_count}"
        )


class Video:
    def __init__(self, video_cache, channel_cache):
        self.video_cache = video_cache
        self.channel_cache = channel_cache
        self.stat_cache = self.get_stats()

        self.title = self.get_video_title()
        self.description = self.get_video_description()
        self.view_count = self.get_view_count()

        self.duration = self.get_video_duration()
        self.publish_date = self.get_video_publish_date()
        self.thumbnails = self.get_video_thumbnail()

        self.tags = self.get_video_tags()
        self.category = self.get_video_category()

        self.video_id = self.get_video_id()
        self.channel_id = self.get_channel_id()

    def __str__(self):
        title = f"title: {self.title}"
        view_count = f"view_count: {self.view_count}"
        duration = f"duration: {self.duration}"
        publish_date = f"publish_date: {self.publish_date}"
        channel_id = f"channel_id: {self.channel_id}"

        return "\n".join([title, view_count, duration, publish_date, channel_id])

    def get_video_title(self):
        return self.video_cache["title"]

    def get_video_description(self):
        return self.video_cache["description"]

    def get_view_count(self):
        return self.video_cache["view_count"]

    def get_video_duration(self):
        return self.video_cache["duration"]

    def get_video_publish_date(self):
        return self.video_cache["publish_date"]

    def get_video_thumbnail(self):
        return self.video_cache['thumbnails']
    
    def get_video_tags(self):
        return self.video_cache["tags"]

    def get_video_category(self):
        return self.video_cache["category"]

    def get_video_id(self):
        return self.video_cache["video_id"]

    def get_channel_id(self):
        return self.channel_cache["channel_id"]

    def get_subscriber_count_of_video_owner(self):
        return self.channel_cache["subscriber_count"]

    def get_stats(self):
        youtube = authenticate()

        info = (
            youtube.channels()
            .list(part="statistics", id=self.channel_cache["channel_id"])
            .execute()
        )

        return info


class SubScraper:
    def __init__(self):
        self.file_name = "channels.json"
        self.channels = [
            Channel(channel["id"])
            for channel in json.loads(open(self.file_name).read())
        ]

    def get_results(self, max_days_old: int, channel_count: int) -> list[Video]:
        videos = []

        # create results.json if it doesn't exist
        if not os.path.exists("videos.json"):
            with open("videos.json", "w") as f:
                f.write("{}")

        with open("videos.json", "r") as f:
            results = json.loads(f.read())

        for channel_index, channel in enumerate(self.channels[:channel_count]):
            for video_index, video_json in enumerate(channel.videos):
                video_id = video_json["videoId"]

                if video_id not in results:
                    response_json = get_video_info(video_json=video_json)
                    results.update(
                        video_id: {
                            'video': {
                                'title': get_video_title(video_json),
                                'description': get_video_description(video_json),
                                'duration': get_video_duration(video_json),
                                'publish_date': get_video_publish_date(response_json),
                                'thumbnails': get_video_thumbnail(response_json),
                                'video_id': get_video_id(video_json),
                                'view_count': get_view_count(video_json),
                                'tags': get_video_tags(response_json),
                                'category': get_video_category(response_json)
                            },
                            'channel': {
                                'channel_id': get_channel_id(response_json),
                                'channel_title': get_channel_title(response_json),
                                'subscriber_count': get_subscriber_count_of_video_owner(channels=self.channels, 
                                                                                        channel_json=response_json)
                            }
                        }
                    )

                video_cache = results[video_id]["video"]
                channel_cache = results[video_id]["channel"]

                video = Video(video_cache=video_cache, channel_cache=channel_cache)
                channel_id = video.get_channel_id()
                channel = get_channel_of_video(
                    channels=self.channels, channel_id=channel_id
                )

                channel.subscriber_count = video.get_subscriber_count_of_video_owner()

                publish_date = datetime.fromisoformat(
                    video.publish_date.replace("Z", "+00:00")
                )
                now = datetime.now(timezone.utc).astimezone()

                days_old = (now - publish_date).days

                if days_old > max_days_old:
                    break

                videos.append(video)
                print(channel_index, video_index)

        with open("videos.json", "w") as f:
            json.dump(results, f, indent=4)

        return videos

    def plot_results(
        self, max_days_old: int, channel_count: int, no_of_bins: int
    ) -> None:
        videos = self.get_results(
            max_days_old=max_days_old, channel_count=channel_count
        )

        views = []
        channel_sub_counts = []

        with open('videos.json', 'r') as f:
            results = json.loads(f.read())

        for video in videos:
            result = results[video.video_id]

            view_count = video.get_view_count()
            channel_sub_count = video.get_subscriber_count_of_video_owner()

            views.append(view_count)
            channel_sub_counts.append(channel_sub_count)

        subscriber_mean = sum(set(channel_sub_counts)) / len(channel_sub_counts)

        normalized_views = [
            view / self.normalize(sub_count, subscriber_mean)
            for view, sub_count in zip(views, channel_sub_counts)
        ]

        plt.hist(normalized_views, bins=no_of_bins)
        plt.xlabel("views")
        plt.ylabel("frequency")
        plt.title(f"Views of videos from the last {max_days_old} days")
        plt.show()

    def normalize(self, subscriber_count, mean):
        # print(subscriber_count, tanh(subscriber_count))
        # print(mean, tanh(mean))

        result = math.log(subscriber_count + 2)
        return result

        # return tanh(subscriber_count) / tanh(mean) * 0.5


class Thumbnail:
    def __init__(self, url, width, height):
        self.url = url
        self.width = width
        self.height = height

    def __str__(self):
        url = f"url: {self.url}"
        width = f"width: {self.width}"
        height = f"height: {self.height}"

        return "\n".join([url, width, height])

    def to_json(self):
        return {"url": self.url, "width": self.width, "height": self.height}


def main():
    subscraper = SubScraper()
    subscraper.plot_results(max_days_old=100, channel_count=20, no_of_bins=5)


if __name__ == "__main__":
    main()
