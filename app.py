import asyncio
from core.audio import Audio
from core.export import Export
from core.translation import Translation
from core.video import GenerateVideo
from core.llm import LLM

async def translate_video(video_path, video_language, target_language):
  video_path = "demo/tr.mp4"
  video_language = "tr"
  target_language = "ar"
  audio_path = Audio().extract_audio(video_path)

  result = Audio().transcribe(audio_path, video_language)
  srt_path = Export().generate_srt(result)

  srt_path = await Translation().translate_srt(srt_path, video_language, target_language, f"temp/result_{target_language}.srt")
  # srt_path = "temp/result_ar.srt"
  
  # Create video generator with optimized settings
  video_gen = GenerateVideo(
    video=video_path,
    subtitles=srt_path, 
    lang=target_language, 
    title=target_language,
    output_file=f"output/output_{target_language}.mp4"
  )
  
  video_gen.generate_video()
  # video_gen.cleanup_temp_files()

def main():
  # asyncio.run(translate_video())
  vocals, instrumental = Audio().separate_audio_with_demucs("temp/audio.mp3")
  print(vocals, instrumental)

if __name__ == "__main__":
  main()