# Playlist2Podcast

[![CI](https://github.com/psidex/playlist2podcast/actions/workflows/main.yml/badge.svg)](https://github.com/psidex/playlist2podcast/actions/workflows/main.yml)
[![Docker Pulls](https://img.shields.io/docker/pulls/psidex/playlist2podcast)](https://hub.docker.com/repository/docker/psidex/playlist2podcast)
[![buymeacoffee donate link](https://img.shields.io/badge/Donate-Beer-FFDD00.svg?style=flat&colorA=35383d)](https://www.buymeacoffee.com/psidex)

A self-hosted application that lets you create podcast RSS feeds from YouTube
playlists.

## What Does This Do?

Takes a list of YouTube playlists and:

- Downloads all the videos in audio only format (best quality)
- Geneartes an RSS XML feed and writes it to a file so that the audio files can
  be used/read by podcast apps

The generated RSS XML file is located at
`podcasts_path/playlist_title/podcast.xml`.

## What Does This Not Do?

This does not actually host the downloaded/created files, you will need a static
web server for that, I reccomend [Caddy](https://caddyserver.com/) or
[nginx](https://www.nginx.com/).

The directory you want to serve is the same one that you put as the
`podcasts_path` config variable.

Once you have that setup you can simply put the URL to each generated
`podcast.xml` into your chosen podcast app, for example
`https://podcasts.example.com/test/podcast.xml` where `test` is the title of the
YouTube playlist.

If the podcast title has special characters you will need to use the URL encoded
text, for example if your YouTube playlist was called `moneypodcast$$$` then the
title gets encoded to `moneypodcast%24%24%24`, which would give you the url
`https://podcasts.example.com/moneypodcast%24%24%24/podcast.xml`.

If you don't know how to do this you can use an online URL encoder such as
[urlencoder.org](https://www.urlencoder.org/).

## Running & Config

Run p2p with `python main.py`, or see below for Docker.

Once running p2p will check for playlist updates once every 24 hours.

p2p will look for a `config.yaml` file where it is run, if running in Docker you
will want to mount it in `/app`, like so:

```bash
-v $(pwd)/config.yaml:/app/config.yaml:ro \
```

Here's what the contents should look like:

```yaml
# The URL that you are going to be hosting the podcast files at.
host_base_url: "https://podcasts.example.com/"

# The path (either on your system or inside the Docker container) that will contain the podcast data.
podcasts_path: "/podcasts"

# The list of playlists to download and host.
podcasts:

  # MUST BE playlist name : playlist URL (NOT a video URL)
  # If the playlist name in this file is incorrect the feed generation wont work.
  test: "https://www.youtube.com/playlist?list=PLTLwdZqDsAvtGmVvJqRS2czLq2YZ_ZHPJ"
```

## Docker

Example run command:

```bash
docker run -d --name p2p --restart unless-stopped \
    -v $(pwd)/config.yaml:/app/config.yaml:ro \
    -v $(pwd)/podcasts:/podcasts \
    psidex/playlist2podcast
```

Don't forget if you're using the Docker build, `podcast_path` in `config.yaml`
should reference the path _inside_ the container, not outside it.

## Credits

Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download the playlists and
[feedgen](https://feedgen.kiesow.be/) to create the RSS XML.
