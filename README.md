# Playlist2Podcast

[![CI](https://github.com/psidex/playlist2podcast/actions/workflows/main.yml/badge.svg)](https://github.com/psidex/playlist2podcast/actions/workflows/main.yml)

A self-hosted application that lets you create podcast RSS feeds from YouTube
playlists.

Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download the playlists and
[feedgen](https://feedgen.kiesow.be/) to create the RSS XML.

## Config

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
  playlist title: "https://www.youtube.com/playlist?list=PLTLwdZqDsAvtGmVvJqRS2czLq2YZ_ZHPJ"
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
