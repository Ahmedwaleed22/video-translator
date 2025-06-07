import asyncio
import os
from core.audio import Audio
from core.export import Export
from core.translation import Translation
from core.video import GenerateVideo
from core.dubbed_video_generation import combine_audio_with_timing

async def translate_video(video_path, video_language, target_language):
  audio_path = Audio().extract_audio(video_path)

  result = Audio().transcribe(audio_path, video_language)
  srt_path = Export().generate_srt(result)

  srt_path = await Translation().translate_srt(srt_path, video_language, target_language, f"temp/result_{target_language}.srt")
  
  video_gen = GenerateVideo(
    video=video_path,
    subtitles=srt_path, 
    lang=target_language, 
    title=target_language,
    output_file=f"output/output_{target_language}.mp4"
  )
  
  video_gen.generate_video()
  video_gen.cleanup_temp_files()

async def dub_video_to_en(video_path, video_language):
  audio_path = Audio().extract_audio(video_path)
  result = Audio().transcribe(audio_path, video_language)
  srt_path = Export().generate_srt(result)
  srt_path = await Translation().translate_srt(srt_path, video_language, "en", f"temp/result_en.srt", f"temp/result_en.txt")
  os.makedirs("temp/dubbed", exist_ok=True)
  with open("temp/result_en.txt", "r", encoding="utf-8") as f:
    lines = f.read()
    lines = lines.split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    for i,line in enumerate(lines):
      translated_audio_path = Audio().generate_translated_audio(audio_path, line, f"temp/dubbed/translated_audio_{i}.wav")
      print(translated_audio_path)

  vocals, instrumental = Audio().separate_audio_from_music(audio_path)

  audio_path = combine_audio_with_timing("temp/dubbed", "temp/result_en.srt", instrumental, "temp/final_combined_audio.wav")
  print(audio_path)

  video_gen = GenerateVideo(
    video=video_path,
    subtitles=None, 
    lang="en", 
    title="en",
    output_file=f"output/output_en.mp4",
    audio=audio_path
  )

  video_gen.generate_video()
  video_gen.cleanup_temp_files()


def main():
  # Translate video to arabic (Subtitles tr -> ar)
  asyncio.run(translate_video("demo/tr.mp4", "tr", "ar"))

  # Dub video to english (Audio tr -> en) (Only english supported for now)
  asyncio.run(dub_video_to_en("demo/tr.mp4", "tr"))

if __name__ == "__main__":
  main()