"""
Enhanced audio generation and processing using Dia TTS for smoother podcast output.
"""

import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydub import AudioSegment
from pydub.silence import detect_silence

from research_podcast.models.settings import Settings
from research_podcast.utils.logging import configure_logging

log = configure_logging()

# Check if Dia TTS is available
try:
    from dia.model import Dia
    DIA_AVAILABLE = True
except ImportError:
    DIA_AVAILABLE = False
    log.warning("Dia TTS not available. Audio generation will be disabled.")

# --- Silence/Audio Tuning Parameters ---
# Make these potentially configurable via Settings if needed
SILENCE_THRESH_DB = -40      # Silence threshold in dBFS
MIN_SILENCE_LEN_MS = 300     # Minimum length of silence to detect (slightly shorter to catch more)
CHUNK_TRANSITION_PAUSE_MS = 0 # Pause duration added between chunks (we'll use crossfade instead)
CHUNK_CROSSFADE_MS = 30      # Crossfade duration between chunks for smoother transitions
TRIM_START_SILENCE_KEEP_MS = 150 # Max silence to keep at the start of a chunk
TRIM_END_SILENCE_KEEP_MS = 200   # Max silence to keep at the end of a chunk
INTERNAL_SILENCE_MAX_MS = 600  # Internal silences longer than this will be shortened
INTERNAL_SILENCE_REPLACE_MS = 350 # Shorten long internal silences to this duration

TARGET_CHUNK_CHAR_LEN = 750 # Target character length for dynamic chunking
MAX_CHUNK_CHAR_LEN = 1000   # Maximum character length before forcing a split

# ---

def to_dia_transcript(dialogue: List[Dict[str, str]]) -> str:
    """
    Convert dialogue dict to Dia's transcript format with speaker tags.

    Args:
        dialogue: List of dialogue exchanges with 'speaker' and 'text' keys

    Returns:
        Formatted transcript string for Dia TTS
    """
    speaker_map = {"Julia": "[S1]", "Guido": "[S2]"}
    lines = []

    for d in dialogue:
        speaker_tag = d.get("speaker")
        text = d.get("text", "").strip()

        if not text:
            continue

        # Ensure speaker tag is present, default to S1 if unknown but exists
        speaker = speaker_map.get(speaker_tag, '[S1]' if speaker_tag else '[S1]')
        # Ensure text doesn't accidentally start with a tag if speaker is missing
        if text.startswith("[S1]") or text.startswith("[S2]"):
             log.warning(f"Dialogue text '{text[:20]}...' seems to already contain a speaker tag. Check input script.")
             lines.append(text) # Assume it's pre-formatted? Risky.
        else:
             lines.append(f"{speaker} {text}")

    return " ".join(lines)

def create_dynamic_chunks(dialogue: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
    """
    Splits dialogue into chunks dynamically based on character length, respecting speaker turns.

    Args:
        dialogue: List of dialogue exchanges.

    Returns:
        List of dialogue chunks (each chunk is a list of exchanges).
    """
    chunks = []
    current_chunk_dialogue = []
    current_chunk_char_count = 0
    speaker_map = {"Julia": "[S1]", "Guido": "[S2]"} # needed for char count estimate

    for i, item in enumerate(dialogue):
        speaker_tag = speaker_map.get(item.get("speaker", "Julia"), "[S1]")
        text = item.get("text", "").strip()
        if not text:
            continue

        # Estimate characters added by this item (tag + space + text)
        item_char_count = len(speaker_tag) + 1 + len(text)

        # Check if adding this item exceeds MAX length, OR
        # if adding exceeds TARGET length AND the chunk already has items
        if current_chunk_dialogue and \
           ((current_chunk_char_count + item_char_count > MAX_CHUNK_CHAR_LEN) or \
            (current_chunk_char_count + item_char_count > TARGET_CHUNK_CHAR_LEN and current_chunk_char_count > 0)):

            # Finalize the current chunk
            chunks.append(current_chunk_dialogue)
            # Start a new chunk
            current_chunk_dialogue = [item]
            current_chunk_char_count = item_char_count
        else:
            # Add to the current chunk
            current_chunk_dialogue.append(item)
            current_chunk_char_count += item_char_count

    # Add the last chunk if it has content
    if current_chunk_dialogue:
        chunks.append(current_chunk_dialogue)

    log.info(f"Split transcript into {len(chunks)} dynamic chunks based on ~{TARGET_CHUNK_CHAR_LEN} chars.")
    return chunks

def process_chunk_silence(audio_segment: AudioSegment) -> AudioSegment:
    """
    Trims excessive silence from the beginning and end of an audio segment
    and shortens long internal silences.

    Args:
        audio_segment: The input AudioSegment.

    Returns:
        The processed AudioSegment.
    """
    # Detect silence segments
    silence_ranges = detect_silence(
        audio_segment,
        min_silence_len=MIN_SILENCE_LEN_MS,
        silence_thresh=SILENCE_THRESH_DB
    )

    processed_audio = audio_segment

    # Trim excessive silence at beginning if present
    if silence_ranges and silence_ranges[0][0] == 0:
        start_silence_duration = silence_ranges[0][1]
        if start_silence_duration > TRIM_START_SILENCE_KEEP_MS:
            trim_amount = start_silence_duration - TRIM_START_SILENCE_KEEP_MS
            processed_audio = processed_audio[trim_amount:]
            log.debug(f"Trimmed {trim_amount}ms from start.")
             # Recalculate silence ranges after trimming
            silence_ranges = detect_silence(
                processed_audio,
                min_silence_len=MIN_SILENCE_LEN_MS,
                silence_thresh=SILENCE_THRESH_DB
            )


    # Trim excessive silence at end if present
    # Need to check against the *potentially modified* length
    current_length = len(processed_audio)
    if silence_ranges and silence_ranges[-1][1] == current_length:
        end_silence_start, end_silence_end = silence_ranges[-1]
        end_silence_duration = end_silence_end - end_silence_start
        if end_silence_duration > TRIM_END_SILENCE_KEEP_MS:
            trim_point = end_silence_start + TRIM_END_SILENCE_KEEP_MS
            processed_audio = processed_audio[:trim_point]
            log.debug(f"Trimmed {current_length - trim_point}ms from end.")
            # Recalculate silence ranges after trimming
            silence_ranges = detect_silence(
                processed_audio,
                min_silence_len=MIN_SILENCE_LEN_MS,
                silence_thresh=SILENCE_THRESH_DB
            )

    # Replace long internal silences with shorter ones
    # Iterate backwards to avoid index issues after modification
    current_length = len(processed_audio) # Update length again
    new_audio = processed_audio # Start building potentially modified audio
    offset = 0 # Keep track of how much length has changed
    indices_to_process = []

    for i in range(len(silence_ranges)):
         start, end = silence_ranges[i]
         # Check if it's internal (not touching start or end of current audio length)
         is_internal = start > 0 and end < current_length
         duration = end - start
         if is_internal and duration > INTERNAL_SILENCE_MAX_MS:
             indices_to_process.append((start,end))


    # Process internal silences modification (if any) - simpler approach
    if indices_to_process:
        final_segments = []
        last_end = 0
        silence_replacement = AudioSegment.silent(duration=INTERNAL_SILENCE_REPLACE_MS)

        for start, end in indices_to_process:
            # Add the segment before the long silence
            final_segments.append(processed_audio[last_end:start])
            # Add the replacement silence
            final_segments.append(silence_replacement)
            log.debug(f"Replaced internal silence {end-start}ms at {start} with {INTERNAL_SILENCE_REPLACE_MS}ms.")
            last_end = end

        # Add the remaining part of the audio after the last replaced silence
        final_segments.append(processed_audio[last_end:])

        # Combine the segments
        processed_audio = sum(final_segments, AudioSegment.empty())


    return processed_audio


def generate_audio(dialogue: List[Dict[str, str]], settings: Settings) -> Optional[str]:
    """
    Generate audio using Dia TTS from dialogue script, dynamically chunking,
    processing silence, and using crossfades for smoother transitions.

    Args:
        dialogue: List of dialogue exchanges with 'speaker' and 'text' keys
        settings: Configuration settings

    Returns:
        Path to the generated WAV file, or None if generation failed
    """
    if not DIA_AVAILABLE:
        log.error("Dia TTS is not available. Audio generation skipped.")
        return None

    output_dir = settings.output_root / "podcast"
    output_dir.mkdir(exist_ok=True, parents=True)
    final_wav = output_dir / "podcast_raw.wav"
    chunk_dir = output_dir / "chunks"
    chunk_dir.mkdir(exist_ok=True, parents=True)

    # Use dynamic chunking
    chunks = create_dynamic_chunks(dialogue)
    if not chunks:
        log.error("Dialogue resulted in zero chunks. Cannot generate audio.")
        return None

    # Check for voice prompts
    audio_prompt = None
    if settings.voice_prompts:
        # Assuming voice_prompts is a dict like {"SpeakerName": "path/to/prompt.wav"}
        # Use the first available prompt path for the initial generation.
        # Dia 1.6B uses a single prompt to condition, not speaker-specific ones during generation.
        first_prompt_path = next(iter(settings.voice_prompts.values()), None)
        if first_prompt_path:
             audio_prompt = Path(first_prompt_path).expanduser()
             if audio_prompt.exists():
                 log.info(f"Using voice prompt for initial chunk: {audio_prompt}")
             else:
                 log.warning(f"Voice prompt file not found: {audio_prompt}. Proceeding without prompt.")
                 audio_prompt = None
        else:
             log.info("No voice prompt path provided in settings.")

    log.info("Loading Dia 1.6B TTS weights...")

    try:
        # Load model once
        model = Dia.from_pretrained("nari-labs/Dia-1.6B", compute_dtype="float16")
        log.info("Dia TTS model loaded successfully")

        # Process each chunk
        chunk_wavs = []
        for i, chunk_dialogue in enumerate(chunks):
            # Convert chunk dialogue to Dia transcript format
            chunk_text = to_dia_transcript(chunk_dialogue)

            if not chunk_text.strip():
                 log.warning(f"Chunk {i+1} is empty after formatting. Skipping.")
                 continue

            log.info(f"Generating audio for chunk {i+1}/{len(chunks)} ({len(chunk_text)} chars)...")

            # Generate audio for this chunk
            generation_args = {
                "temperature": settings.temperature or 0.7, # Use setting temperature if available
                "top_p": 0.9,
            }
            # Use audio prompt only for the very first chunk to set the voice
            if audio_prompt and i == 0:
                generation_args["audio_prompt"] = str(audio_prompt)
                log.info("Applying audio prompt to first chunk.")


            start_time = time.time()
            output = model.generate(chunk_text, **generation_args)
            end_time = time.time()
            log.info(f"Chunk {i+1} generated in {end_time - start_time:.2f} seconds.")

            # Save chunk temporarily
            chunk_path = chunk_dir / f"chunk_{i:03d}.wav" # Use more digits if many chunks expected
            model.save_audio(str(chunk_path), output)
            log.info(f"Saved raw chunk {i+1} to {chunk_path}")

            chunk_wavs.append(str(chunk_path))

        # Combine chunks with silence processing and crossfading
        log.info("Combining audio chunks, optimizing silence, and applying crossfades...")
        combined = AudioSegment.empty()

        for i, wav_path in enumerate(chunk_wavs):
            try:
                chunk_audio = AudioSegment.from_file(wav_path)
            except Exception as e:
                log.error(f"Error loading chunk {wav_path}: {e}. Skipping.")
                continue

            # Process silence within the chunk (trimming, shortening)
            log.debug(f"Processing silence for chunk {i+1}...")
            processed_chunk_audio = process_chunk_silence(chunk_audio)

            if not combined:
                # First chunk
                combined = processed_chunk_audio
            else:
                # Apply crossfade from the end of 'combined' to the start of 'processed_chunk_audio'
                log.debug(f"Applying {CHUNK_CROSSFADE_MS}ms crossfade between chunks.")
                combined = combined.append(processed_chunk_audio, crossfade=CHUNK_CROSSFADE_MS)

                # Optional: Add a very small explicit pause *if* crossfade isn't enough (unlikely needed)
                # if CHUNK_TRANSITION_PAUSE_MS > 0:
                #    combined += AudioSegment.silent(duration=CHUNK_TRANSITION_PAUSE_MS)


        # Save combined audio
        log.info(f"Saving combined and processed audio to {final_wav}")
        combined.export(str(final_wav), format="wav")

        log.info("Raw audio generation and combination complete.")
        return str(final_wav)

    except Exception as e:
        log.error(f"Error during audio generation pipeline: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")
        return None

def encode_mp3(wav_path: str, settings: Settings) -> Optional[str]:
    """
    Convert WAV to final MP3 with loudness normalization and metadata.

    Args:
        wav_path: Path to the input WAV file
        settings: Configuration settings

    Returns:
        Path to the generated MP3 file, or None if encoding failed
    """
    if not wav_path or not Path(wav_path).exists():
        log.error(f"Input WAV path is invalid or file does not exist: {wav_path}")
        return None

    output_dir = settings.output_root / "podcast"
    output_dir.mkdir(exist_ok=True, parents=True) # Ensure output dir exists
    final_mp3 = output_dir / "podcast_final.mp3"

    try:
        log.info(f"Loading processed WAV from {wav_path}")
        audio = AudioSegment.from_file(wav_path)

        # Normalize audio gain - ADJUST AS NEEDED
        # Standard practice is loudness normalization (LUFS), but pydub doesn't do it directly.
        # Applying a fixed gain reduction is simpler but less precise.
        # -3dB might be safer than -2dB to avoid clipping after MP3 encoding.
        target_gain_db = -3.0
        log.info(f"Applying {target_gain_db}dB gain adjustment (simple normalization)")
        audio = audio.apply_gain(target_gain_db)

        # Add metadata
        metadata_tags = {
                "title": settings.podcast_title or "AI Research Podcast", # Use settings if available
                "artist": "ResPodGen - Dia 1.6B & Ollama",
                "album": "Research Paper Podcasts",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "comment": f"Generated by ResPodGen. Model: {settings.model_name}. Temp: {settings.temperature}." # Use model_name
            }
        log.info(f"Exporting to MP3: {final_mp3} with metadata.")
        audio.export(
            str(final_mp3),
            format="mp3",
            bitrate="192k", # Standard podcast bitrate
            tags=metadata_tags
        )

        log.info("MP3 encoding complete.")
        return str(final_mp3)

    except Exception as e:
        log.error(f"Error encoding MP3: {e}")
        log.error(f"Traceback: {traceback.format_exc()}")
        return None

