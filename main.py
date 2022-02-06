import datetime
import json
import logging
import os
import re
import time
import unicodedata
import urllib.parse
from pathlib import Path

import pytz
import yaml
import yt_dlp
from feedgen.feed import FeedGenerator


def slugify(value, allow_unicode=False):
    """
    Taken from https://stackoverflow.com/a/295466/6396652
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def getdesc(infodict):
    desc = infodict["description"]
    if desc == "":
        return "No description found."
    return desc


class podcast:
    def __init__(self, playlist_url: str) -> None:
        """Contains information about a podcast.

        Args:
            playlist_url (str): The URL to the YouTube playlist
        """
        self.playlist_url = playlist_url
        self.playlist_meta = {}

        # To be filled later.
        self.playlist_title = "Unknown"

        # Where to download the podcast.
        # All strings in hosted_path after the hostname should use urllib.parse.quote.
        self.hosted_path = ""

        # Where it is on our filesystem.
        self.local_path = ""


class playlist2podcast:
    def __init__(self, config: dict) -> None:
        self.config = config

        self.PODCASTS_PATH = Path(config["podcasts_path"])
        self.HOST_BASE_URL = config["host_base_url"]
        self.DATE_AFTER = config.get("dateafter")  # optional parameter

        if self.HOST_BASE_URL[-1] != "/":
            self.HOST_BASE_URL += "/"

        logging.info("Getting information for podcasts")
        self.podcasts = [
            self.load_meta(podcast(playlist_url))
            for playlist_url in self.config["podcasts"]
        ]

    def update(self):
        """Update all podcasts."""
        logging.info("Updating podcasts")
        for pod in self.podcasts:
            logging.info(f"Updating playlist download for {pod.playlist_title}")
            self.dl(pod)
            logging.info(f"Generating feed XML for {pod.playlist_title}")
            self.feedify(pod)
            logging.info(f"Finished processing for {pod.playlist_title}")

    def load_meta(self, pod: podcast) -> podcast:
        """Load meta information for a podcast from the YouTube playlist link.

        Args:
            pod (podcast): The podcast object to fill

        Returns:
            podcast: The filled podcast object
        """
        with yt_dlp.YoutubeDL() as ydl:
            meta = ydl.extract_info(pod.playlist_url, download=False, process=False)

            pod.playlist_meta = meta
            pod.playlist_title = meta["title"]

            # slugify makes its safe for fs, urllib quote makes it safe for urls.
            title_slugged = slugify(meta["title"])
            pod.hosted_path = f"{self.HOST_BASE_URL}{urllib.parse.quote(title_slugged)}"
            pod.local_path = self.PODCASTS_PATH.joinpath(title_slugged)

        return pod

    def dl(self, pod: podcast) -> None:
        """Use yt-dlp to read playlist and download all non-dowloaded videos (as audio).

        Args:
            ffmpeg_path (str): Path to ffmpeg binary
            pod (podcast): The podcast object we are downloading for
        """
        download_directory = pod.local_path

        ydl_opts = {
            "download_archive": str(download_directory.joinpath("downloaded.txt")),
            "outtmpl": str(download_directory.joinpath("%(title)s.%(ext)s")),
            "ignoreerrors": True,
            "format": "bestaudio/best",
            "writeinfojson": True,
        }

        if self.DATE_AFTER:
            ydl_opts["daterange"] = yt_dlp.DateRange(start=self.DATE_AFTER, end=None)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([pod.playlist_url])

    def feedify(self, pod: podcast) -> None:
        """For the given podcast directory, generate an RSS file.

        Args:
            pod (podcast): The podcast object we are processing for
        """
        podcast_dir = pod.local_path

        fg = FeedGenerator()

        fg.title(pod.playlist_meta["title"])
        fg.description(getdesc(pod.playlist_meta))
        fg.author({"name": pod.playlist_meta["uploader"]})
        fg.link(href=pod.playlist_meta["webpage_url"], rel="alternate")

        thumbnail_url = ""
        thumbnail_biggest_pixel_count = 0
        for thumb in pod.playlist_meta["thumbnails"]:
            if thumb.get("id") == "avatar_uncropped":
                thumbnail_url = thumb["url"]
                break
            pixel_count = thumb.get("height", 0) * thumb.get("width", 0)
            if pixel_count > thumbnail_biggest_pixel_count:
                thumbnail_url = thumb["url"]
                thumbnail_biggest_pixel_count = pixel_count

        fg.logo(thumbnail_url)

        fg.load_extension("podcast")
        fg.podcast.itunes_category("Podcasting")

        for file in os.listdir(podcast_dir):
            if file.endswith(".webm"):
                filename = os.path.splitext(file)[0]

                with open(podcast_dir.joinpath(f"{filename}.info.json"), "r") as jsonf:
                    fileinfo = json.load(jsonf)

                download_url = f"{pod.hosted_path}/{urllib.parse.quote(file)}"

                fe = fg.add_entry()
                fe.id(download_url)
                fe.title(fileinfo["title"])
                fe.description(getdesc(fileinfo))
                fe.enclosure(download_url, str(fileinfo["filesize"]), "audio/webm")

                upload_date = fileinfo["upload_date"]
                upload_date = (
                    f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                )
                upload_datetime = datetime.datetime.strptime(upload_date, "%Y-%m-%d")
                upload_datetime = pytz.utc.localize(upload_datetime)
                fe.pubDate(upload_datetime.strftime("%a, %d %b %Y %H:%M:%S %z"))

        fg.rss_str(pretty=True)
        fg.rss_file(str(podcast_dir.joinpath("podcast.xml")))


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s",
    )

    with open("./config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as err:
            logging.error(f"Failed to load config: {err}")
            return

    logging.info(config)

    p = playlist2podcast(config)

    while True:
        p.update()
        time.sleep(60 * 60 * 24)


if __name__ == "__main__":
    main()
