import typer
import subprocess
import os
import shutil
import re
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys

app = typer.Typer(help="YoutubeMusic-USB: Synchronize YouTube Music playlists to a USB drive, optimized for car audio systems.")
console = Console()

def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return
    spotdl_ffmpeg = Path.home() / ".spotdl" / "ffmpeg.exe"
    if spotdl_ffmpeg.exists():
        return
    with console.status("[bold blue]Downloading initial dependency (FFmpeg)...[/bold blue]"):
        try:
            subprocess.run([sys.executable, "-m", "spotdl", "--download-ffmpeg"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, input=b"n\n")
        except subprocess.CalledProcessError:
            console.print("[bold red]Error installing FFmpeg. Ensure you have an active internet connection.[/bold red]")
            raise typer.Exit(1)

def ensure_deno():
    with console.status("[bold blue]Downloading bypass dependency (Deno)...[/bold blue]"):
        try:
            subprocess.run([sys.executable, "-m", "spotdl", "--download-deno"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, input=b"n\n")
        except subprocess.CalledProcessError:
            pass

def sanitize_filename(name: str) -> str:
    import unicodedata
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    name = re.sub(r'[^a-zA-Z0-9 \-_]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def organize_directory(usb_path: Path, audio_format: str, safe_chars: bool, group_by_artist: bool, alpha_order: bool):
    if safe_chars:
        console.print("[bold blue]Applying automotive compatibility (--safe-chars)...[/bold blue]")
        for root, dirs, files in os.walk(usb_path):
            if ".spotdl" in root: continue
            for file in files:
                if file.endswith(f".{audio_format}"):
                    old_path = Path(root) / file
                    new_name = sanitize_filename(old_path.stem) + old_path.suffix
                    new_path = Path(root) / new_name
                    if old_path != new_path and not new_path.exists():
                        old_path.rename(new_path)
        if group_by_artist:
            for root, dirs, files in os.walk(usb_path, topdown=False):
                for dir_name in dirs:
                    old_dir = Path(root) / dir_name
                    new_dir = Path(root) / sanitize_filename(dir_name)
                    if old_dir != new_dir and not new_dir.exists():
                        old_dir.rename(new_dir)

    if alpha_order:
        console.print("[bold blue]Enumerating songs in alphabetical order (--alpha-order)...[/bold blue]")
        for root, dirs, files in os.walk(usb_path):
            if ".spotdl" in root: continue
            audio_files = [f for f in files if f.endswith(f".{audio_format}")]
            if not audio_files: continue
            
            file_map = []
            for f in audio_files:
                clean_name = re.sub(r'^\d+\s*-\s*', '', f)
                file_map.append((clean_name, f))
            
            file_map.sort(key=lambda x: x[0].lower())
            
            for idx, (clean_name, orig_name) in enumerate(file_map, start=1):
                new_name = f"{str(idx).zfill(3)} - {clean_name}"
                if new_name != orig_name:
                    orig_path = Path(root) / orig_name
                    new_path = Path(root) / new_name
                    if not new_path.exists():
                        orig_path.rename(new_path)

    console.print("[bold blue]Cleaning up empty folders...[/bold blue]")
    for root, dirs, files in os.walk(usb_path, topdown=False):
        for dir_name in dirs:
            try:
                (Path(root) / dir_name).rmdir()
            except OSError:
                pass

@app.command("sync")
def sync(
    url: str = typer.Argument(..., help="YouTube Music playlist URL"),
    usb_path: Path = typer.Argument(..., help="Destination path or USB drive (e.g., E:\\Music)"),
    group_by_artist: bool = typer.Option(False, "--group-by-artist", help="Create individual folders for each artist"),
    clean_names: bool = typer.Option(False, "--clean-names", help="Standardize names to 'Artist - Title'"),
    safe_chars: bool = typer.Option(False, "--safe-chars", help="Remove accents and emojis for compatibility with older stereos"),
    sync_mode: bool = typer.Option(False, "--sync", help="Download only missing tracks from the destination folder"),
    audio_format: str = typer.Option("mp3", "--format", help="Audio format (mp3, m4a, flac, etc.)"),
    alpha_order: bool = typer.Option(False, "--alpha-order", help="Enumerate songs from 001 to infinity in alphabetical order")
):
    """Downloads and synchronizes songs from a YouTube Music playlist."""
    console.print(f"[bold green]Starting YoutubeMusic-USB (Download Phase)[/bold green]")
    ensure_ffmpeg()
    ensure_deno()

    if not usb_path.exists():
        console.print(f"[bold yellow]Destination folder '{usb_path}' does not exist. Creating it now...[/bold yellow]")
        usb_path.mkdir(parents=True, exist_ok=True)

    filename_template = "{title}"
    if clean_names and not group_by_artist:
        filename_template = "{artist} - {title}"

    if group_by_artist:
        output_template = f"{usb_path}/{{artist}}/{filename_template}"
    else:
        output_template = f"{usb_path}/{filename_template}"

    command = [sys.executable, "-m", "spotdl"]
    if sync_mode:
        command.append("sync")
        save_file = usb_path / "playlist_sync.spotdl"
        command.extend([url, "--save-file", str(save_file)])
    else:
        command.append(url)
        
    command.extend([
        "--format", audio_format,
        "--output", output_template,
        "--bitrate", "320k" if audio_format == "mp3" else "auto",
        "--simple-tui", 
        "--ytm-data"
    ])
    
    console.print(f"[bold blue]Executing YouTube Music download (This may take a few minutes to search for all songs)...[/bold blue]")
    
    env = os.environ.copy()
    spotdl_path = str(Path.home() / ".spotdl")
    env["PATH"] = f"{spotdl_path}{os.pathsep}{env.get('PATH', '')}"
    
    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError:
        console.print("[bold red]An error occurred while downloading the songs.[/bold red]")
        raise typer.Exit(1)

    organize_directory(usb_path, audio_format, safe_chars, group_by_artist, alpha_order)
    console.print(f"[bold green]Successfully completed! Your songs are located at: {usb_path}[/bold green]")

@app.command("organize")
def organize(
    usb_path: Path = typer.Argument(..., help="Destination path or USB drive containing the songs"),
    safe_chars: bool = typer.Option(False, "--safe-chars", help="Remove accents and emojis for compatibility with older stereos"),
    alpha_order: bool = typer.Option(True, "--alpha-order", help="Enumerate songs from 001 to infinity in alphabetical order"),
    group_by_artist: bool = typer.Option(False, "--group-by-artist", help="Only used to rename artist folders in safe-chars mode"),
    audio_format: str = typer.Option("mp3", "--format", help="Audio format of the files to organize")
):
    """Organizes songs in an existing folder (Alphabetical order and Safe-chars) without downloading anything new."""
    console.print(f"[bold green]Starting YoutubeMusic-USB (Organization Phase)[/bold green]")
    if not usb_path.exists():
        console.print(f"[bold red]Error: The folder '{usb_path}' does not exist.[/bold red]")
        raise typer.Exit(1)
        
    organize_directory(usb_path, audio_format, safe_chars, group_by_artist, alpha_order)
    console.print(f"[bold green]Organization successfully completed![/bold green]")

if __name__ == "__main__":
    app()
