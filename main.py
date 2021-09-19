import json
import logging
import os
import time
import urllib.parse
from pathlib import Path

import yaml
import yt_dlp
from feedgen.feed import FeedGenerator

# TODO: Keep playlist order (see playlist_index), add thumbnail(s).


def getdesc(infodict):
    desc = infodict["description"]
    if desc == "":
        return "No description found."
    return desc


class podcast:
    def __init__(
        self, name: str, playlist_url: str, hosted_path: str, local_path: str
    ) -> None:
        """Contains information about a podcast.

        Args:
            name (str): The name of the podcast (i.e. the name of the playlist)
            playlist_url (str): The URL to the YouTube playlist
            hosted_path (str): The URL where this podcast will be hosted
            local_path (str): The path to where the data for this podcas tis
        """
        self.name = name
        self.playlist_url = playlist_url
        self.hosted_path = hosted_path
        self.local_path = local_path


class playlist2podcast:
    def __init__(self, config: dict) -> None:
        self.config = config

        self.PODCASTS_PATH = Path(config["podcasts_path"])
        self.HOST_BASE_URL = config["host_base_url"]

        if self.HOST_BASE_URL[-1] != "/":
            self.HOST_BASE_URL += "/"

        self.podcasts = [
            podcast(
                name,
                playlist_url,
                f"{self.HOST_BASE_URL}{name}",
                self.PODCASTS_PATH.joinpath(name),
            )
            for name, playlist_url in self.config["podcasts"].items()
        ]

    def update(self):
        """Update all podcasts."""
        logging.info("Updating podcasts")
        for pod in self.podcasts:
            logging.info(f"Updating playlist download for {pod.name}")
            self.dl(pod)
            logging.info(f"Generating feed XML for {pod.name}")
            self.feedify(pod)
            logging.info(f"Finished processing for {pod.name}")

    def dl(self, pod: podcast) -> None:
        """Use yt-dlp to read playlist and download all non-dowloaded videos (as audio).

        Args:
            ffmpeg_path (str): Path to ffmpeg binary
            pod (podcast): The podcast object we are downloading for
        """
        download_directory = Path(pod.local_path)
        ydl_opts = {
            "download_archive": str(download_directory.joinpath("downloaded.txt")),
            "outtmpl": str(download_directory.joinpath("%(title)s.%(ext)s")),
            "ignoreerrors": True,
            "format": "bestaudio/best",
            "writeinfojson": True,
            "allow_playlist_files": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([pod.playlist_url])

    def feedify(self, pod: podcast) -> None:
        """For the given podcast directory, generate an RSS file.

        Args:
            pod (podcast): The podcast object we are processing for
        """
        podcast_dir = Path(pod.local_path)

        try:
            # NOTE: This only works if pod.name is also the name of the playlist.
            with open(podcast_dir.joinpath(f"{pod.name}.info.json"), "r") as jsonf:
                podinfo = json.load(jsonf)
        except FileNotFoundError:
            logging.error("Config error: The config playlist name must match exactly")
            return

        fg = FeedGenerator()

        fg.title(podinfo["title"])
        fg.description(getdesc(podinfo))
        fg.author({"name": podinfo["uploader"]})
        fg.link(href=podinfo["webpage_url"], rel="alternate")

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
