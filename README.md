# YoutubeMusic-USB (YTM-USB)

A powerful, robust command-line tool designed to download and synchronize YouTube Music playlists directly to USB drives, specifically optimized for older car audio systems.

## Features

- **Automated YouTube Music Downloads**: Fetches high-quality audio directly from YouTube Music playlists.
- **Car Audio Compatibility**: Formats and sanitizes filenames (removes emojis, accents, and special characters) so legacy car stereos can read them without errors (`--safe-chars`).
- **Alphabetical Ordering**: Automatically prepends sequential track numbers (e.g., `001 - `, `002 - `) based on alphabetical sorting to force your car stereo to play tracks in order (`--alpha-order`).
- **Smart Synchronization**: Only downloads new tracks added to your playlist, avoiding duplicate downloads (`--sync`).
- **Artist Grouping**: Optionally organizes downloaded tracks into neat folders by artist (`--group-by-artist`).
- **Clean Names**: Optionally standardizes track names to `Artist - Title.mp3` format (`--clean-names`).

## Installation

Ensure you have [uv](https://github.com/astral-sh/uv) installed, then clone the repository and sync the environment:

```bash
git clone https://github.com/FelipeRochaMartins/Spotify-to-USB.git
cd Spotify-to-USB
uv sync
```

## Usage

The tool exposes a global `ytm-usb` command with two subcommands: `sync` and `organize`.

### 1. Downloading and Synchronizing (`sync`)

Downloads a playlist and automatically applies all selected formatting and organization rules.

```bash
uv run ytm-usb sync "YOUTUBE_MUSIC_PLAYLIST_URL" "C:\Path\To\USB" [OPTIONS]
```

**Recommended Command for Car Stereos:**
```bash
uv run ytm-usb sync "https://music.youtube.com/playlist?list=YOUR_LIST" "E:\Musicas" --clean-names --safe-chars --sync --alpha-order
```

**Options:**
- `--group-by-artist`: Creates individual folders for each artist.
- `--clean-names`: Formats filenames to `Artist - Title`.
- `--safe-chars`: Strips special characters, accents, and emojis.
- `--sync`: Skips already downloaded files and only fetches new ones.
- `--alpha-order`: Enumerates tracks (001, 002...) in alphabetical order.
- `--format`: Audio format (default is `mp3`).

### 2. Organizing Existing Folders (`organize`)

If you already have a folder full of MP3s and just want to apply the automotive compatibility rules (like stripping special characters and enumerating them), use the `organize` command. This does **not** require an internet connection and will not download anything.

```bash
uv run ytm-usb organize "C:\Path\To\USB" [OPTIONS]
```

**Example:**
```bash
uv run ytm-usb organize "E:\Musicas" --safe-chars --alpha-order
```

## How It Works Under The Hood

This tool utilizes `spotdl` and `yt-dlp` to power the audio extraction and metadata tagging, while fully bypassing traditional API limits by strictly leveraging YouTube Music endpoints. FFmpeg and Deno are automatically provisioned in the background during the first run to ensure a seamless experience.

## License

MIT
