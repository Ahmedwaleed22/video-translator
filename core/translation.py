import pysrt
from translate import Translator

class Translation:
  def translate_text(self, text, from_language, target_language):
    translator = Translator(to_lang=target_language, from_lang=from_language)
    text = translator.translate(text)
    return text

  def translate_srt(self, srt_path, from_language, target_language, output_path):
    subs = pysrt.open(srt_path)

    for sub in subs:
      sub.text = self.translate_text(sub.text, from_language, target_language)

    subs.save(output_path, encoding='utf-8')
    return output_path
