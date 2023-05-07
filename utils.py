from config import set_values
from subscraper import Thumbnail, Video, Channel
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError



set_values()
developer_key = os.getenv('YOUTUBE_API_KEY')
api_service_name = "youtube"
api_version = "v3"


def authenticate():
    youtube = build(api_service_name,
                    api_version,
                    developerKey=developer_key)

    return youtube


def get_view_count_from_video_json(video_json: str) -> int:
    def convert_view_count(view_count: str) -> int:
        return int(view_count.replace('.', ''))

    temp_count = video_json['viewCountText']['simpleText'].split()[0]
    return convert_view_count(temp_count)


def get_max_res_thumbnail(thumbnails: list[Thumbnail]) -> Thumbnail:
    max_res = thumbnails[0]
    for thumbnail in thumbnails:
        if thumbnail.width > max_res.width:
            max_res = thumbnail

    return max_res


def get_video_info(video_json: str) -> str:
    youtube = authenticate()

    info = youtube.videos().list(
        part="snippet",
        id=video_json['videoId']
    ).execute()

    return info


def get_channel_of_video(channels: list[Channel], video: Video) -> Channel:
    for channel in channels:
        if channel.channel_id == video.channel_id:
            return channel
    
    # if channel does not exist, return None
    return None


def get_channel_id_from_response_json(response_json: str) -> str:
    return response_json['items'][0]['snippet']['channelId']


def get_stat_from_response_json(response_json: str) -> str:
    youtube = authenticate()

    channel_id = get_channel_id_from_response_json(response_json)

    # if video is not processed before
    info = youtube.channels().list(
        part="statistics",
        id=channel_id
    ).execute()

    return info


def get_subscriber_count_of_video_owner(channels: list[Channel], video: Video) -> int:
    channel = get_channel_of_video(channels=channels, video=video)

    if channel.subscriber_count is not None:
        return channel.subscriber_count
    
    stat_json = get_stat_from_response_json(video.response_json)
    subscriber_count = get_subscriber_count_from_json(stat_json)

    return subscriber_count


def get_subscriber_count_from_json(stat_json: str) -> int:
    def convert_view_count(view_count: str) -> int:
        return int(view_count.replace('.', ''))
    
    sub_count_str = stat_json['items'][0]['statistics']['subscriberCount']
    return convert_view_count(sub_count_str)


def get_channel_stat_info(response_json: str) -> str:
    youtube = authenticate()

    channel_id = get_channel_id_from_response_json(response_json)

    # if video is not processed before
    info = youtube.channels().list(
        part="statistics",
        id=channel_id
    ).execute()

    return info


