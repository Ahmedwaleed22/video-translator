import pysrt
from translate import Translator
import argostranslate.package
import argostranslate.translate
import logging

class Translation:
  def __init__(self):
    self.logger = logging.getLogger(__name__)

  def translate_text(self, text, from_lang='en', to_lang='ar'):
    try:
      translatedText = argostranslate.translate.translate(text, from_lang, to_lang)
      return translatedText
    except RuntimeError as e:
      if "model.bin is incomplete" in str(e):
        raise RuntimeError(f"Translation model for {from_lang}->{to_lang} is corrupted or missing. Please run 'python install_languages.py' to reinstall the language package.")
      else:
        raise e
    except Exception as e:
      self.logger.error(f"Translation failed for text '{text}': {e}")
      raise e

  def translate_srt(self, srt_path, from_language, target_language, output_path):
    try:
      subs = pysrt.open(srt_path)

      for sub in subs:
        sub.text = self.translate_text(sub.text, from_language, target_language)

      subs.save(output_path, encoding='utf-8')
      return output_path
    except Exception as e:
      self.logger.error(f"SRT translation failed: {e}")
      raise e
