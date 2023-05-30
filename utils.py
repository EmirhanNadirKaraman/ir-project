from config import set_values
from subscraper import Thumbnail, Channel
import os

from googleapiclient.discovery import build


set_values()
developer_key = os.getenv("YOUTUBE_API_KEY")
api_service_name = "youtube"
api_version = "v3"


def authenticate():
    youtube = build(api_service_name, api_version, developerKey=developer_key)

    return youtube


def get_view_count(video_json: str) -> int:
    def convert_view_count(view_count: str) -> int:
        return int(view_count.replace(".", ""))

    temp_count = video_json["viewCountText"]["simpleText"].split()[0]
    return convert_view_count(temp_count)


def get_max_res_thumbnail(thumbnails: list[Thumbnail]) -> Thumbnail:
    max_res = thumbnails[0]
    for thumbnail in thumbnails:
        if thumbnail.width > max_res.width:
            max_res = thumbnail

    return max_res


def get_video_info(video_json: str) -> str:
    youtube = authenticate()

    try:
        info = youtube.videos().list(part="snippet", id=video_json["videoId"]).execute()
    except:
        youtube = authenticate()
        info = youtube.videos().list(part="snippet", id=video_json["videoId"]).execute()

    return info


def get_channel_of_video(channels: list[Channel], channel_id: str) -> Channel:
    for channel in channels:
        if channel.channel_id == channel_id:
            return channel

    # if channel does not exist, return None
    return None


def get_channel_id(channel_json: str) -> str:
    return channel_json["items"][0]["snippet"]["channelId"]


def get_stats(channel_cache):
    youtube = authenticate()

    info = (
        youtube.channels()
        .list(part="statistics", id=channel_cache["channel_id"])
        .execute()
    )

    return info


def get_stats_from_response(channel_json: str) -> str:
    youtube = authenticate()

    channel_id = get_channel_id(channel_json)

    # if video is not processed before
    info = youtube.channels().list(part="statistics", id=channel_id).execute()

    return info


def get_subscriber_count_of_video_owner(
    channels: list[Channel], channel_json: str
) -> int:
    channel_id = get_channel_id(channel_json=channel_json)
    channel = get_channel_of_video(channels=channels, channel_id=channel_id)

    if channel is None:
        print("hey what the helll")

    if channel.subscriber_count is not None:
        return channel.subscriber_count

    stat_json = get_stats_from_response(channel_json)
    subscriber_count = get_subscriber_count_from_response(stat_json)

    return subscriber_count


def get_subscriber_count_from_response(stat_json: str) -> int:
    def convert_view_count(view_count: str) -> int:
        return int(view_count.replace(".", ""))

    sub_count_str = stat_json["items"][0]["statistics"]["subscriberCount"]
    return convert_view_count(sub_count_str)


def get_channel_stat_info(channel_json: str) -> str:
    youtube = authenticate()

    channel_id = get_channel_id(channel_json)

    # if video is not processed before
    info = youtube.channels().list(part="statistics", id=channel_id).execute()

    return info


def get_video_category(channel_json) -> str:
    return channel_json["items"][0]["snippet"]["categoryId"]


def get_video_tags(channel_json) -> list[str]:
    return channel_json["items"][0]["snippet"].get("tags", None)


def get_video_title(video_json):
    return video_json["title"]["runs"][0]["text"]


def get_video_description(video_json):
    return video_json["descriptionSnippet"]["runs"][0]["text"]


def get_video_duration(video_json):
    return video_json["thumbnailOverlays"][0]["thumbnailOverlayTimeStatusRenderer"][
        "text"
    ]["simpleText"]


def get_video_publish_date(channel_json):
    return channel_json["items"][0]["snippet"]["publishedAt"]


def get_video_thumbnail(channel_json) -> list[Thumbnail]:

    default_res = channel_json['items'][0]['snippet']['thumbnails'].get('default', None)
    max_res = channel_json['items'][0]['snippet']['thumbnails'].get('maxres', default_res)

    thumbnail = Thumbnail(url=max_res['url'], 
                          width=max_res['width'], 
                          height=max_res['height']).to_json()

    return thumbnail


def get_video_id(video_json) -> str:
    return video_json["videoId"]


def get_channel_title(channel_json) -> str:
    return channel_json["items"][0]["snippet"]["title"]
