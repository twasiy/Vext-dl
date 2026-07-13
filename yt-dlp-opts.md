# Playlist Options

```bash
1. --no-playlist        # Donwload only the video if the url referes both video and a playlist
2. --yes-playlist       # Download the playlist if the url referes both video and a playlist
3. --playlist-random    # Download playlist videos in random order
4. --playlist-items     # Download playlsit specified videos. expect comma separated value. can use python slice notation for range, skip, etc...
5. --playlist-reverse   # Download playlist in reverse order. use python slice notation `::-1`
```

# Download Options

```bash
1. --concurrent-fragments   # Number of fragmets of a video should be downloaded concurrently
2. --limit-rate             # Maximum limit bytes per second (e.g, 50K or 4.2M)
3. --retries                # Number of retries (default 10 or infinite)
4. --file-access-retries    # Number of file access error retries (default 3 or infinite)
5. --fragment-retries       # Number of retries for a framgement (default 10 or infinite)
```

# File system Options

```bash
1. --batch-file         # File containing url to download. one url per line. `#`, `;`, `]` considered as comment
2. --output             # Output filname template
3. --paths              # The path whare the file should be downloaded
4. --write-description  # Write video description to a .description file
5. --write-info-json    # Write video metadata to a .info.json file
6. --cookies            # Cookie file
7. --write-thumbnail    # Write thumbnail image to disk
8. --write-subs         # Write subtitle file
9. --list-subs          # List all subtitles
```

# Verbosity and Simulation Options

```bash
1. --quiet      # Activate quite mode
2. --verbose    # Print verbose debugging information
```

# Video Format Options

```bash
1. --format         # Video format to specify
2. --list-formats   # List available formats of each video
```

# Post-Processing Options

```bash
1. --extract-audio      # Convert video file to audio
2. --audio-format       # Format to convert the audio. (currently supported: best (default),aac, alac, flac, m4a, mp3, opus, vorbis,wav)
3. --audio-quality      # specify ffmpeg audio quality in 0(best)-10(wrost) (default 5) or specific bitrate(e.g, 128K, 192K)
4. --remux-video        # Remux a video into another container.
                        # (currently supported: avi, flv, gif, mkv, mov, mp4, webm, aac, aiff, alac, flac, m4a, mka, mp3, ogg, opus, vorbis, wav)
5. --embed-subs         # Embed subtitles into the video
6. --embed-thumbnail    # Embed thumbnail into the video
7. --embed-metadata     # Embed metadata into the video
```


# Common options
- Output folder / output template
- Thumbnail (write thumbnail, embed thumbnail)
- Subtitles (write subtitles, embed subtitles, auto subtitles)
- Metadata (embed metadata, write description, write info json)
- Proxy
- Cookies file
- Retries (extractor retries, fragment retries)
- Concurrent fragment downloads
- Rate limit / speed limit
- Quiet / verbose / progress bar settings
- Overwrite files / no-overwrite
- Playlist range / playlist items / playlist start / playlist end
- Sponsorblock / skip chapters
- User agent
- HTTP headers
- Sleep interval / sleep requests
- Download archive (to avoid re-downloading)
