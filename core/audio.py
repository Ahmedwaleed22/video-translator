from moviepy.video.io.VideoFileClip import VideoFileClip
import whisper_timestamped as whisper

class Audio:
  def extract_audio(self, video_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile("temp/audio.mp3")
    
    return "temp/audio.mp3"
  
  def transcribe(self, audio_path):
    audio = whisper.load_audio(audio_path)
    model = whisper.load_model("base")

    result = whisper.transcribe(model, audio, language="en")

    # print(json.dumps(result, indent = 2, ensure_ascii = False))
    return result