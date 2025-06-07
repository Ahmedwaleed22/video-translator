import asyncio
import os
from core.audio import Audio
from core.export import Export
from core.translation import Translation
from core.video import GenerateVideo
from core.llm import LLM
from core.dubbed_video_generation import combine_audio_with_timing

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

async def dub_video_to_en(video_path, video_language):
  audio_path = Audio().extract_audio(video_path)
  # result = Audio().transcribe(audio_path, video_language)
  # srt_path = Export().generate_srt(result)
  # srt_path = await Translation().translate_srt(srt_path, video_language, "en", f"temp/result_en.srt", f"temp/result_en.txt")
  # os.makedirs("temp/dubbed", exist_ok=True)
  # with open("temp/result_en.txt", "r", encoding="utf-8") as f:
  #   lines = f.read()
  #   lines = lines.split("\n")
  #   lines = [line.strip() for line in lines if line.strip()]

  #   for i,line in enumerate(lines):
  #     translated_audio_path = Audio().generate_translated_audio(audio_path, line, f"temp/dubbed/translated_audio_{i}.wav")
  #     print(translated_audio_path)

  # vocals, instrumental = Audio().separate_audio_with_demucs(audio_path)
  # print(vocals, instrumental)

  combine_audio_with_timing("temp/dubbed", "temp/result_en.srt", "temp/demucs_output/htdemucs/audio/no_vocals.wav", "temp/final_combined_audio.wav")


def main():
  # asyncio.run(translate_video())
  # vocals, instrumental = Audio().separate_audio_with_demucs("temp/audio.mp3")
  # print(vocals, instrumental)
  # asyncio.run(translate_video())
  asyncio.run(dub_video_to_en("demo/tr.mp4", "tr"))

  # Audio().generate_translated_audio("temp/audio.mp3", "Hello Ahmed, How are you?")

if __name__ == "__main__":
  main()