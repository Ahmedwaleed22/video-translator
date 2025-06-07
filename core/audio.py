from moviepy.video.io.VideoFileClip import VideoFileClip
import whisper_timestamped as whisper
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import os
import subprocess

class Audio:
  def extract_audio(self, video_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile("temp/audio.mp3")
    
    return "temp/audio.mp3"
  
  def transcribe(self, audio_path, language="en"):
    audio = whisper.load_audio(audio_path)
    model = whisper.load_model("base")

    result = whisper.transcribe(model, audio, language=language)

    # print(json.dumps(result, indent = 2, ensure_ascii = False))
    return result
  
  def separate_audio_with_demucs(self, audio_path):
    """
    Separate audio using Demucs (modern, state-of-the-art source separation)
    Returns paths to vocals and instrumental tracks
    """
    try:
      # Create output directory if it doesn't exist
      os.makedirs("temp/demucs_output", exist_ok=True)
      
      # Run demucs separation
      cmd = [
        "python", "-m", "demucs.separate",
        "--two-stems=vocals",  # Separate into vocals and accompaniment
        "-o", "temp/demucs_output",
        audio_path
      ]
      
      subprocess.run(cmd, check=True, capture_output=True)
      
      # Find the output files (demucs creates subdirectories)
      audio_name = os.path.splitext(os.path.basename(audio_path))[0]
      base_dir = f"temp/demucs_output/mdx_extra/{audio_name}"
      
      vocals_path = f"{base_dir}/vocals.wav"
      instrumental_path = f"{base_dir}/no_vocals.wav"
      
      # Copy to temp directory with standard names
      if os.path.exists(vocals_path):
        subprocess.run(["cp", vocals_path, "temp/vocals_demucs.wav"], check=True)
      if os.path.exists(instrumental_path):
        subprocess.run(["cp", instrumental_path, "temp/instrumental_demucs.wav"], check=True)
      
      return "temp/vocals_demucs.wav", "temp/instrumental_demucs.wav"
      
    except subprocess.CalledProcessError as e:
      print(f"Demucs separation failed: {e}")
      # Fallback to librosa method
      return self.separate_audio_from_music(audio_path)
    except Exception as e:
      print(f"Error in Demucs separation: {e}")
      # Fallback to librosa method
      return self.separate_audio_from_music(audio_path)

  def separate_audio_from_music(self, audio_path):
    y, sr = librosa.load(audio_path, sr=44100)
    
    # Method 1: Harmonic-Percussive Source Separation + center extraction
    y_harmonic, y_percussive = librosa.effects.hpss(y, margin=(1.0, 5.0))
    
    # Extract center channel (where vocals typically sit in stereo mix)
    if len(y.shape) > 1:  # if stereo
        y_center = y[0] - y[1]  # simple center extraction
    else:
        y_center = y
    
    # Create spectrograms
    S_full = librosa.stft(y_center, hop_length=512)
    S_harmonic = librosa.stft(y_harmonic, hop_length=512)
    
    # Improved separation using multiple techniques
    
    # 1. Median filtering for repetitive background removal
    S_filter = librosa.decompose.nn_filter(np.abs(S_full), 
                                          aggregate=np.median, 
                                          metric='cosine',
                                          width=int(sr/512))  # adaptive window
    
    # 2. Conservative margins - preserve more music
    freq_bins = librosa.fft_frequencies(sr=sr, n_fft=2048)
    vocal_range = (freq_bins >= 200) & (freq_bins <= 800)  # narrower vocal range
    
    # More conservative margins to preserve instruments
    margin_v = np.ones_like(freq_bins) * 1.5  # less aggressive vocal extraction
    margin_i = np.ones_like(freq_bins) * 0.3  # much more conservative instrument removal
    
    # Only slightly boost core vocal frequencies
    margin_v[vocal_range] = 2.5
    margin_i[vocal_range] = 0.5  # preserve instruments even in vocal range
    
    # 3. Gentler masking to preserve more instruments
    S_abs = np.abs(S_full)
    S_diff = np.maximum(0, S_abs - S_filter * 0.5)  # less aggressive filtering
    
    # Create masks with frequency-dependent margins
    mask_v = librosa.util.softmask(S_diff, 
                                  margin_i[:, np.newaxis] * S_filter, 
                                  power=1.5)  # gentler power
    mask_i = librosa.util.softmask(S_filter, 
                                  margin_v[:, np.newaxis] * S_diff, 
                                  power=1.5)
    
    # Ensure instrumental track retains most of the original
    mask_i = np.maximum(mask_i, 0.2)  # always keep at least 20% of original
    
    # 4. Apply temporal smoothing to reduce artifacts
    from scipy.ndimage import median_filter
    mask_v = median_filter(mask_v, size=(1, 3))  # smooth in time
    mask_i = median_filter(mask_i, size=(1, 3))
    
    # Apply masks
    S_foreground = mask_v * S_full
    S_background = mask_i * S_full
    
    # Convert back to audio with overlap-add
    y_foreground = librosa.istft(S_foreground, hop_length=512)
    y_background = librosa.istft(S_background, hop_length=512)
    
    # Post-processing: preserve low frequencies for instruments
    y_foreground = librosa.effects.preemphasis(y_foreground)  # emphasize high freq for vocals
    
    # Add back some low-end to instrumental track
    y_background_lowpass = librosa.effects.preemphasis(y_background, coef=-0.97)  # boost low freq
    
    # Normalize to prevent clipping
    y_foreground = y_foreground / (np.max(np.abs(y_foreground)) + 1e-8)
    y_background_lowpass = y_background_lowpass / (np.max(np.abs(y_background_lowpass)) + 1e-8)
    
    # Save with higher quality
    sf.write('temp/vocals.wav', y_foreground, sr, subtype='PCM_24')
    sf.write('temp/instrumental.wav', y_background_lowpass, sr, subtype='PCM_24')
    
    return "temp/vocals.wav", "temp/instrumental.wav"

# Alternative method focusing on center-channel extraction
def separate_vocals_center_extraction(self, audio_path):
    """Simpler approach focusing on stereo center extraction"""
    y, sr = librosa.load(audio_path, mono=False)
    
    if y.shape[0] == 2:  # stereo
        # Center extraction (vocals) and sides (instruments)
        center = (y[0] + y[1]) / 2
        sides = (y[0] - y[1]) / 2
        
        # Enhance separation with spectral gating
        S_center = librosa.stft(center)
        S_sides = librosa.stft(sides)
        
        # Simple spectral gating
        magnitude_center = np.abs(S_center)
        magnitude_sides = np.abs(S_sides)
        
        # Create masks based on which channel is dominant
        mask_vocals = magnitude_center > (magnitude_sides * 1.5)
        mask_instruments = magnitude_sides > (magnitude_center * 0.8)
        
        # Apply masks
        vocals = librosa.istft(S_center * mask_vocals)
        instruments = librosa.istft(S_sides * mask_instruments + S_center * ~mask_vocals)
        
    else:  # mono - fall back to spectral method
        vocals, instruments = self.separate_audio_from_music(audio_path)
        return vocals, instruments
    
    # Normalize and save
    vocals = vocals / (np.max(np.abs(vocals)) + 1e-8)
    instruments = instruments / (np.max(np.abs(instruments)) + 1e-8)
    
    sf.write('temp/vocals_center.wav', vocals, sr)
    sf.write('temp/instrumental_center.wav', instruments, sr)
    
    return "temp/vocals_center.wav", "temp/instrumental_center.wav"