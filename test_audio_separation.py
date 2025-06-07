#!/usr/bin/env python3
"""
Test script for audio separation using different methods
"""

from core.audio import Audio
import os

def test_audio_separation():
    # Initialize audio processor
    audio_processor = Audio()
    
    # You can test with any audio file
    # For this example, we'll assume you have an audio file
    test_audio_path = "temp/audio.mp3"  # This would be created by extract_audio()
    
    if not os.path.exists(test_audio_path):
        print("No test audio file found. Please extract audio from a video first.")
        print("Example: audio_processor.extract_audio('your_video.mp4')")
        return
    
    print("Testing different audio separation methods...")
    
    # Method 1: Demucs (recommended - state-of-the-art)
    print("\n1. Testing Demucs separation...")
    try:
        vocals_demucs, instrumental_demucs = audio_processor.separate_audio_with_demucs(test_audio_path)
        print(f"✅ Demucs separation successful!")
        print(f"   Vocals: {vocals_demucs}")
        print(f"   Instrumental: {instrumental_demucs}")
    except Exception as e:
        print(f"❌ Demucs separation failed: {e}")
    
    # Method 2: Librosa (fallback method)
    print("\n2. Testing Librosa separation...")
    try:
        vocals_librosa, instrumental_librosa = audio_processor.separate_audio_from_music(test_audio_path)
        print(f"✅ Librosa separation successful!")
        print(f"   Vocals: {vocals_librosa}")
        print(f"   Instrumental: {instrumental_librosa}")
    except Exception as e:
        print(f"❌ Librosa separation failed: {e}")
    
    # Method 3: Center extraction (simple method)
    print("\n3. Testing center extraction...")
    try:
        vocals_center, instrumental_center = audio_processor.separate_vocals_center_extraction(test_audio_path)
        print(f"✅ Center extraction successful!")
        print(f"   Vocals: {vocals_center}")
        print(f"   Instrumental: {instrumental_center}")
    except Exception as e:
        print(f"❌ Center extraction failed: {e}")

if __name__ == "__main__":
    test_audio_separation() 