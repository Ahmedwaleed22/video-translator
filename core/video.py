import ffmpeg
import os
import pysubs2
import re

class GenerateVideo:
    def __init__(self, video, subtitles, lang, title, output_file="output.mp4"):
        self.video = video
        self.subtitles = subtitles
        self.lang = lang
        self.title = title
        self.output_file = output_file
        self.ass_file = f"temp/temp_subs_{self.lang}.ass"

    def is_rtl_language(self):
        rtl_languages = ['ar', 'he', 'fa', 'ur', 'yi', 'iw', 'ji', 'ps', 'sd']
        return self.lang in rtl_languages

    def get_font_config(self):
        font_configs = {
            'ar': {'font_name': 'Noto Sans Arabic', 'font_size': 24, 'fontsdir': os.path.abspath('fonts')},
            'he': {'font_name': 'Noto Sans Hebrew', 'font_size': 20, 'fontsdir': os.path.abspath('fonts')},
            'fa': {'font_name': 'Noto Sans Arabic', 'font_size': 22, 'fontsdir': os.path.abspath('fonts')},
            'ur': {'font_name': 'Noto Sans Arabic', 'font_size': 22, 'fontsdir': os.path.abspath('fonts')},
            'en': {'font_name': 'SF Pro Text', 'font_size': 16, 'fontsdir': None},
            'es': {'font_name': 'SF Pro Text', 'font_size': 16, 'fontsdir': None},
            'fr': {'font_name': 'SF Pro Text', 'font_size': 16, 'fontsdir': None},
            'de': {'font_name': 'SF Pro Text', 'font_size': 16, 'fontsdir': None},
            'zh': {'font_name': 'PingFang SC', 'font_size': 16, 'fontsdir': None},
            'ja': {'font_name': 'Hiragino Sans', 'font_size': 16, 'fontsdir': None},
            'ko': {'font_name': 'Apple SD Gothic Neo', 'font_size': 16, 'fontsdir': None}
        }
        return font_configs.get(self.lang, font_configs['en'])

    import re

    def convert_srt_to_ass(self, srt_file, ass_file, font_config, is_rtl):
        subs = pysubs2.load(srt_file, encoding="utf-8")

        style = pysubs2.SSAStyle()
        style.fontname = font_config['font_name']
        style.fontsize = font_config['font_size']
        style.primarycolor = pysubs2.Color(255, 255, 255, 0)
        style.outlinecolor = pysubs2.Color(0, 0, 0, 0)
        style.backcolor = pysubs2.Color(0, 0, 0, 255)
        style.bold = False
        style.italic = False
        style.shadow = 1
        style.outline = 1
        style.marginv = 10
        style.alignment = 2
        style.encoding = 1

        if is_rtl:
            style.alignment = 2  # Bottom center

        subs.styles["Default"] = style

        # Unicode directional markers
        LRE = "\u202A"  # Left-to-Right Embedding
        RLE = "\u202B"  # Right-to-Left Embedding
        PDF = "\u202C"  # Pop Directional Formatting

        for line in subs:
            if is_rtl:
                # Wrap English substrings in LRE...PDF
                line.text = re.sub(
                    r'([A-Za-z0-9_\/\\\:\.\,\-\+]+)',
                    lambda m: LRE + m.group(1) + PDF,
                    line.text
                )
                # Optionally wrap whole line in RLE...PDF
                line.text = RLE + line.text + PDF

        subs.save(ass_file)

    def generate_video(self):
        font_config = self.get_font_config()
        is_rtl = self.is_rtl_language()

        self.convert_srt_to_ass(self.subtitles, self.ass_file, font_config, is_rtl)

        input_video = ffmpeg.input(self.video)

        subtitle_filter_args = {'fontsdir': font_config['fontsdir']} if font_config['fontsdir'] else {}

        video_with_subs = ffmpeg.filter(
            input_video['v'],
            'subtitles',
            self.ass_file,
            **subtitle_filter_args
        )

        output_ffmpeg = ffmpeg.output(
            video_with_subs, input_video['a'],
            self.output_file,
            vcodec='libx264',
            acodec='copy',
            metadata=f'title={self.title}'
        )

        output_ffmpeg = ffmpeg.overwrite_output(output_ffmpeg)
        print(ffmpeg.compile(output_ffmpeg))
        ffmpeg.run(output_ffmpeg)

    def cleanup_temp_files(self):
        if os.path.exists(self.ass_file):
            os.remove(self.ass_file)