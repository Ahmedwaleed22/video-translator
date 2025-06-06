from core.audio import Audio
from core.export import Export
from core.translation import Translation
from core.video import GenerateVideo

def main():
  video_path = "demo/1.mp4"
  language = "ar"
  audio_path = Audio().extract_audio(video_path)

  result = Audio().transcribe(audio_path)
  srt_path = Export().generate_srt(result)

  srt_path = Translation().translate_srt(srt_path, "en", language, f"temp/result_{language}.srt")
  
  # Create video generator with optimized settings
  video_gen = GenerateVideo(
    video=video_path, 
    subtitles=srt_path, 
    lang=language, 
    title=language,
    output_file=f"output/output_{language}.mp4"
  )
  
  video_gen.generate_video()
  video_gen.cleanup_temp_files()

if __name__ == "__main__":
    main()