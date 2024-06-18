def gen_commands(
    yt_dlp_command: list[str],
    whisper_command: str,
    count_video_files_command: str,
) -> list[str]:
    """
    Generate a list of commands to be executed.

    Args:
        yt_dlp_command (list[str]): A list of commands related to yt-dlp.
        whisper_command (str): A command related to whisper.
        gen_count_video_files_command (str): A command to generate count of video files.

    Returns:
        list[str]: A list of commands to be executed.
    """
    commands: list[str] = (
        [
            "rm -rf video/",
            "pip install yt-dlp",
            "sudo apt-get update --allow-releaseinfo-change",
            "sudo apt-get install -y file",
        ]
        + yt_dlp_command
        + [
            count_video_files_command,
            "git clone https://huggingface.co/spaces/aadnk/whisper-webui",
            whisper_command,
            'find video -type f \( -name "*.json" -o -name "*.txt" -o -name "*.vtt" \) -exec rm {} \;',
            "rm -rf whisper-webui/",
        ]
    )
    return commands


def gen_yt_dlp_command(
    video_url: str,
    video_output_template: str = "%(title)s.%(ext)s",
    geo_bypass_country: str = "JP",
    age_limit: int = 0,
    video_format: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
) -> str:
    """
    Generates a command string for downloading a YouTube video using yt-dlp or wget.

    Args:
        video_url (str): The URL of the YouTube video to download.
        video_output_template (str, optional): The output template for the downloaded video file. Defaults to "%(title)s.%(ext)s".
        geo_bypass_country (str, optional): The country code to bypass geographic restrictions. Defaults to "JP".
        age_limit (int, optional): The age limit for the video. Defaults to 0.
        video_format (str, optional): The desired video format. Defaults to "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best".

    Returns:
        str: The command string for downloading the YouTube video.
    """
    return (
        f'yt-dlp --paths video/ --output "{video_output_template}" '
        + f"--geo-bypass-country {geo_bypass_country} "
        + f"--age-limit {age_limit} "
        + f'--format "{video_format}" '
        + f'"{video_url}" || '
        + f'wget -P video/ "{video_url}" || exit 0'
    )


def gen_count_video_files_command(max_files: int = 1) -> str:
    """
    Generates a command that counts the number of video and audio files in the 'video' directory.

    Args:
        max_files (int): The maximum number of video files allowed.

    Returns:
        str: The generated command as a string.
    """
    return (
        f'[ $(find video -type f -exec file --mime-type -b {{}} + | grep -E "video/|audio/" | wc -l) -eq 0 ] || '
        + f'[ $(find video -type f -exec file --mime-type -b {{}} + | grep -E "video/|audio/" | wc -l) -gt {max_files} ] && exit 1 || exit 0'
    )


def gen_whisper_command(
    output_dir: str = "video",
    model: str = "large-v3",
    vad: str = "none",
    word_timestamps: bool = True,
    initial_prompt: str = "",
    whisper_implementation: str = "faster-whisper",
) -> str:
    """
    Generate the command for running the Whisper.

    Args:
        output_dir (str): The output directory for the generated videos. Defaults to "video".
        model (str): The Whisper model to use. Defaults to "large-v3".
        vad (str): The Voice Activity Detection (VAD) mode. Defaults to "none".
        word_timestamps (bool): Whether to use word timestamps. Defaults to True.
        initial_prompt (str): The initial prompt for the Whisper. Defaults to an empty string.
        whisper_implementation (str): The Whisper implementation to use. Defaults to "faster-whisper".

    Returns:
        str: The generated command for running the Whisper system.
    """
    return (
        f'cd whisper-webui && pip install -r requirements-{"fasterWhisper" if whisper_implementation == "faster-whisper" else whisper_implementation}.txt '
        + "&& find ../video -type f -exec "
        + f"python cli.py --whisper_implementation {whisper_implementation} "
        + f'--output_dir "../{output_dir}" --model {model} --vad {vad} --word_timestamps {word_timestamps} '
        + f'--initial_prompt "{initial_prompt}" "{{}}" +'
    )
