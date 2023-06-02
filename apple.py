import json
import math

from matplotlib import pyplot as plt

with open("videos1.json", "r") as f:
    results = json.loads(f.read())


def normalize(self, subscriber_count):
    scaling_factor = 40

    result = subscriber_count**scaling_factor
    return result


def plot_results(no_of_bins: int) -> None:
    views = []
    channel_sub_counts = []

    for video in results.values():
        view_count = video["video"]["view_count"]
        channel_sub_count = video["channel"]["subscriber_count"]

        views.append(view_count)
        channel_sub_counts.append(channel_sub_count)

        print(view_count, channel_sub_count)

    normalized_views = [
        math.tanh(math.log(view) / math.log(sub_count)) * no_of_bins
        for view, sub_count in zip(views, channel_sub_counts)
    ]

    print(len(normalized_views))

    plt.hist(normalized_views, bins=no_of_bins)
    plt.xlabel("views")
    plt.ylabel("frequency")
    plt.title(f"Views of videos")
    plt.show()


def plot_channels(no_of_bins: int) -> None:
    channels = []
    sub_counts = []
    for video in results.values():
        if video["channel"]["channel_id"] in channels:
            continue

        channels.append(video["channel"]["channel_id"])
        sub_counts.append(video["channel"]["subscriber_count"])

    plt.hist(sub_counts, bins=no_of_bins)
    plt.xlabel("subs")
    plt.ylabel("frequency")
    plt.title(f"Channel subs")
    plt.show()


plot_results(no_of_bins=20)
# plot_channels(no_of_bins=5)
