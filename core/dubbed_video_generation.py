import os
import re
import subprocess
from pathlib import Path
import math

def parse_srt_file(srt_path):
    """Parse SRT file and return list of subtitle entries with timing info."""
    with open(srt_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split by double newlines to separate subtitle blocks
    blocks = re.split(r'\n\s*\n', content.strip())
    subtitles = []
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            # Extract sequence number
            seq_num = int(lines[0])
            
            # Extract timing
            timing_line = lines[1]
            start_time, end_time = timing_line.split(' --> ')
            
            # Convert SRT time format to seconds
            start_seconds = srt_time_to_seconds(start_time)
            end_seconds = srt_time_to_seconds(end_time)
            
            subtitles.append({
                'sequence': seq_num,
                'start': start_seconds,
                'end': end_seconds,
                'duration': end_seconds - start_seconds,
                'text': ' '.join(lines[2:])
            })
    
    return subtitles

def srt_time_to_seconds(time_str):
    """Convert SRT time format (HH:MM:SS,mmm) to seconds."""
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def get_audio_volume_rms(audio_file):
    """Get the RMS volume level of an audio file using FFmpeg with more accurate detection."""
    try:
        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-af', 'astats=metadata=1:reset=1',
            '-f', 'null',
            '-',
            '-v', 'error'  # Reduce verbosity
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Parse the RMS level from FFmpeg stderr output
        output = result.stderr
        rms_values = []
        
        for line in output.split('\n'):
            if 'RMS level dB:' in line:
                # Extract the dB value
                try:
                    db_value = float(line.split('RMS level dB:')[1].strip())
                    rms_values.append(db_value)
                except (ValueError, IndexError):
                    continue
        
        if rms_values:
            # Return average RMS if multiple channels
            return sum(rms_values) / len(rms_values)
        
        # Fallback to volumedetect if astats fails
        return get_audio_volume_fallback(audio_file)
        
    except Exception as e:
        print(f"Warning: Could not detect volume for {audio_file}: {e}")
        return get_audio_volume_fallback(audio_file)

def get_audio_volume_fallback(audio_file):
    """Fallback volume detection using volumedetect."""
    try:
        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-af', 'volumedetect',
            '-f', 'null',
            '-',
            '-v', 'info'
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        output = result.stderr
        
        # Look for mean_volume first (most accurate)
        for line in output.split('\n'):
            if 'mean_volume:' in line:
                db_value = float(line.split('mean_volume:')[1].split('dB')[0].strip())
                return db_value
        
        # If mean_volume not found, look for max_volume
        for line in output.split('\n'):
            if 'max_volume:' in line:
                db_value = float(line.split('max_volume:')[1].split('dB')[0].strip())
                return db_value - 6  # Rough estimate of mean from max
        
        return -20  # Default fallback
    except Exception:
        return -20

def calculate_volume_adjustments(audio_files, target_db=-12, use_peak_normalization=False):
    """
    Calculate volume adjustments to normalize all audio files to the same level.
    
    Args:
        audio_files: List of audio file paths
        target_db: Target dB level (default -12 dB for good headroom)
        use_peak_normalization: If True, normalize to peak level instead of RMS
    """
    print("Analyzing audio volumes...")
    volumes = {}
    
    for i, audio_file in enumerate(audio_files):
        if use_peak_normalization:
            current_db = get_peak_volume(audio_file)
            print(f"Track {i}: {current_db:.1f} dB (peak)")
        else:
            current_db = get_audio_volume_rms(audio_file)
            print(f"Track {i}: {current_db:.1f} dB (RMS)")
        
        volumes[i] = current_db
    
    # Calculate adjustments to reach target dB level
    adjustments = {}
    for i, current_db in volumes.items():
        # Handle -inf dB (silence)
        if current_db == float('-inf') or current_db < -60:
            adjustments[i] = 1.0  # Don't amplify silence
            print(f"Track {i}: Silent track, no adjustment")
            continue
            
        # Calculate the multiplier needed to reach target dB
        db_difference = target_db - current_db
        
        # Limit maximum amplification to prevent distortion
        if db_difference > 20:  # Don't amplify by more than 20 dB
            db_difference = 20
            print(f"Track {i}: Limiting amplification to +20 dB")
        
        # Convert dB to linear scale
        multiplier = 10 ** (db_difference / 20)
        adjustments[i] = multiplier
        
        final_db = current_db + (20 * math.log10(multiplier))
        print(f"Track {i}: {current_db:.1f} dB -> {final_db:.1f} dB (x{multiplier:.2f})")
    
    return adjustments

def get_peak_volume(audio_file):
    """Get the peak volume level of an audio file."""
    try:
        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-af', 'volumedetect',
            '-f', 'null',
            '-',
            '-v', 'info'
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        output = result.stderr
        for line in output.split('\n'):
            if 'max_volume:' in line:
                db_value = float(line.split('max_volume:')[1].split('dB')[0].strip())
                return db_value
        
        return -20  # Default fallback
    except Exception:
        return -20

def get_audio_files(folder_path):
    """Get all translated_audio_*.wav files from the folder."""
    folder = Path(folder_path)
    audio_files = []
    
    # Find all files matching the pattern
    for file in folder.glob('translated_audio_*.wav'):
        # Extract the number from filename
        match = re.search(r'translated_audio_(\d+)\.wav', file.name)
        if match:
            num = int(match.group(1))
            audio_files.append((num, str(file)))
    
    # Sort by number
    audio_files.sort(key=lambda x: x[0])
    return [file_path for _, file_path in audio_files]

def combine_audio_with_timing(audio_folder, srt_path, background_music_path=None, output_path="final_output.wav", 
                            auto_normalize=True, target_volume_db=-12, use_peak_normalization=False, 
                            use_compressor=True):
    """
    Combine audio files according to SRT timing and optionally add background music.
    
    Args:
        audio_folder: Path to folder containing translated_audio_*.wav files
        srt_path: Path to SRT file with timing information
        background_music_path: Optional path to background music file
        output_path: Output file path
        auto_normalize: Whether to automatically normalize all audio to the same volume level
        target_volume_db: Target volume level in dB (default -12 for good headroom)
        use_peak_normalization: Use peak instead of RMS normalization
        use_compressor: Apply audio compression for more consistent levels
    """
    
    # Parse SRT file
    subtitles = parse_srt_file(srt_path)
    
    # Get audio files
    audio_files = get_audio_files(audio_folder)
    
    if len(audio_files) != len(subtitles):
        print(f"Warning: Found {len(audio_files)} audio files but {len(subtitles)} subtitle entries")
        print("This might cause sync issues.")
    
    # Calculate total duration
    total_duration = max(sub['end'] for sub in subtitles)
    
    print(f"Total duration: {total_duration:.3f} seconds")
    print(f"Found {len(audio_files)} audio files")
    print(f"Found {len(subtitles)} subtitle entries")
    
    # Get volume adjustments
    if auto_normalize:
        print(f"Auto-normalizing audio volumes to {target_volume_db} dB...")
        volume_adjustments = calculate_volume_adjustments(
            audio_files, 
            target_db=target_volume_db,
            use_peak_normalization=use_peak_normalization
        )
    else:
        volume_adjustments = None
    
    # Create FFmpeg filter complex for combining audio at specific times
    filter_parts = []
    input_args = []
    
    # Add all audio files as inputs
    for i, audio_file in enumerate(audio_files):
        input_args.extend(['-i', audio_file])
    
    # Add background music if provided
    music_input_index = len(audio_files)
    if background_music_path:
        input_args.extend(['-i', background_music_path])
    
    # Create silence base track
    filter_parts.append(f"aevalsrc=0:duration={total_duration}:sample_rate=44100:channel_layout=stereo[silence]")
    
    # Overlay each audio file at its specific time with volume normalization and optional compression
    current_mix = "silence"
    for i, (audio_file, subtitle) in enumerate(zip(audio_files, subtitles)):
        delay_ms = int(subtitle['start'] * 1000)  # Convert to milliseconds
        
        # Determine volume for this track
        if volume_adjustments and i in volume_adjustments:
            volume = volume_adjustments[i]
        else:
            volume = 1.0  # Default volume (no change)
        
        # Build filter chain for this track
        filter_chain = f"[{i}]"
        
        # Add volume adjustment
        filter_chain += f"volume={volume}"
        
        # Add compressor for more consistent levels (optional)
        if use_compressor:
            # Gentle compression: threshold=-18dB, ratio=3:1, attack=3ms, release=50ms
            filter_chain += ",acompressor=threshold=-18dB:ratio=3:attack=3:release=50:makeup=2dB"
        
        # Add delay
        filter_chain += f",adelay={delay_ms}|{delay_ms}[delayed{i}]"
        
        filter_parts.append(filter_chain)
        
        # Mix with previous result
        filter_parts.append(f"[{current_mix}][delayed{i}]amix=inputs=2:duration=longest:normalize=0[mix{i}]")
        current_mix = f"mix{i}"
    
    # Add background music if provided
    if background_music_path:
        # Loop the background music to match total duration
        filter_parts.append(f"[{music_input_index}]aloop=loop=-1:size=2e+09[bgloop]")
        filter_parts.append(f"[bgloop]atrim=duration={total_duration}[bg]")
        
        # Mix background music with the voice track (keep voice prominent)
        filter_parts.append(f"[bg]volume=3[bg_quiet]")  # Very quiet background music
        filter_parts.append(f"[{current_mix}][bg_quiet]amix=inputs=2:duration=longest:weights=1 0.3[final]")
        output_map = "[final]"
    else:
        output_map = f"[{current_mix}]"
    
    # Combine all filter parts
    filter_complex = ";".join(filter_parts)
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file
    ] + input_args + [
        '-filter_complex', filter_complex,
        '-map', output_map,
        '-c:a', 'pcm_s16le',  # Use WAV format
        '-ar', '44100',  # Sample rate
        output_path
    ]
    
    print("Running FFmpeg command...")
    print(" ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Successfully created: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        print(f"Error output: {e.stderr}")
        return False