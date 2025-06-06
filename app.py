from core.audio import Audio
from core.export import Export
from core.translation import Translation
from core.video import GenerateVideo

def main():
  video_path = "demo/1.mp4"
  # audio_path = Audio().extract_audio(video_path)

  # result = Audio().transcribe(audio_path)
  # srt_path = Export().generate_srt(result)

  # srt_path = Translation().translate_srt(srt_path, "en", "ar", "temp/result_ar.srt")
  srt_path = "temp/result_ar.srt"
  
  # Create video generator with optimized settings
  video_gen = GenerateVideo(
    video=video_path, 
    subtitles=srt_path, 
    lang="ar", 
    title="Arabic",
  )
  
  # Use the fast generation method for maximum speed
  video_gen.generate_video()
  
  # Alternative: Use standard mode for better quality
  # print("🎯 Using STANDARD MODE for balanced speed/quality...")
  # video_gen.generate_video()
  
  # Clean up temporary files
  video_gen.cleanup()

if __name__ == "__main__":
    main()