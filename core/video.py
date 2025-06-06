import ffmpeg
import os

class GenerateVideo:
  def __init__(self, video, subtitles, lang, title, output_file = "output.mp4"):
    self.video = video
    self.subtitles = subtitles
    self.lang = lang
    self.title = title
    self.output_file = output_file

  def get_font_config(self):
    """Get font configuration based on language"""
    font_configs = {
      'ar': {  # Arabic
        'font_name': 'Noto Sans Arabic',
        'font_size': 24,
        'fontsdir': os.path.abspath('fonts')  # Use system font
      },
      'en': {  # English
        'font_name': 'SF Pro Text',
        'font_size': 16,
        'fontsdir': None  # Use system font
      },
      'es': {  # Spanish
        'font_name': 'SF Pro Text',
        'font_size': 16,
        'fontsdir': None
      },
      'fr': {  # French
        'font_name': 'SF Pro Text',
        'font_size': 16,
        'fontsdir': None
      },
      'de': {  # German
        'font_name': 'SF Pro Text',
        'font_size': 16,
        'fontsdir': None
      },
      'zh': {  # Chinese
        'font_name': 'PingFang SC',
        'font_size': 16,
        'fontsdir': None
      },
      'ja': {  # Japanese
        'font_name': 'Hiragino Sans',
        'font_size': 16,
        'fontsdir': None
      },
      'ko': {  # Korean
        'font_name': 'Apple SD Gothic Neo',
        'font_size': 16,
        'fontsdir': None
      }
    }
    
    # Default to English if language not found
    return font_configs.get(self.lang, font_configs['en'])

  def add_custom_font_support(self, lang_code, font_name, font_size=16, fonts_dir=None):
    """Add support for a custom font for a specific language"""
    # This method can be called to add support for additional languages
    # For example: video_gen.add_custom_font_support('hi', 'Noto Sans Devanagari', 16, 'fonts/hindi')
    pass

  def generate_video(self):
    input_video = ffmpeg.input(self.video)
    
    # Get font configuration for the specified language
    font_config = self.get_font_config()
    
    # Prepare subtitle filter arguments
    subtitle_args = [
      input_video['v'],
      'subtitles',
      self.subtitles
    ]
    
    # Add fontsdir if specified (for custom fonts)
    subtitle_kwargs = {}
    if font_config['fontsdir']:
      subtitle_kwargs['fontsdir'] = font_config['fontsdir']
    
    # Configure subtitle styling
    force_style = (
      f"FontName={font_config['font_name']},"
      f"FontSize={font_config['font_size']},"
      "PrimaryColour=&H00FFFFFF,"
      "OutlineColour=&H00000000,"
      "BorderStyle=1,"
      "Outline=1,"
      "Shadow=1,"
      "Alignment=2,"
      "MarginV=30"
    )
    
    subtitle_kwargs['force_style'] = force_style
    
    # Burn subtitles into the video using the subtitles filter
    video_with_subs = ffmpeg.filter(*subtitle_args, **subtitle_kwargs)

    # Create the output with burned-in subtitles
    output_ffmpeg = ffmpeg.output(
        video_with_subs, input_video['a'],
        self.output_file,
        vcodec='libx264',  # Need to re-encode video to burn in subtitles
        acodec='copy',     # Keep audio as-is
        metadata=f'title={self.title}'
    )

    # If the destination file already exists, overwrite it.
    output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)

    # Print the equivalent ffmpeg command we could run to perform the same action as above.
    print(ffmpeg.compile(output_ffmpeg))

    # Do it! transcode!
    ffmpeg.run(output_ffmpeg)

  def cleanup_temp_files(self):
    for i in os.listdir("temp"):
      os.remove(f"temp/{i}")