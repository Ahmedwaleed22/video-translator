import pysrt
import asyncio
import logging
from .llm import LLM
import os

class Translation:
  def __init__(self):
    self.logger = logging.getLogger(__name__)
    self.llm = LLM()

  async def translate_text(self, text, from_lang='en', to_lang='ar'):
    try:
      # Create a translation prompt for the LLM
      messages = [
        {
          "role": "user",
          "content": f"Translate the following text from {from_lang} to {to_lang}. Don't translate terms like 'Vibe Coding' or any terms like that that shouldn't be translated. Return only the translated text without any additional commentary:\n\n{text}"
        }
      ]
      
      # Use the LLM to translate
      translated_text = self.llm.generate_response(
        messages=messages,
        model=os.getenv('OPENROUTER_LLM_MODEL')
      )
      
      return translated_text.strip()
    except Exception as e:
      self.logger.error(f"Translation failed for text '{text}': {e}")
      raise e

  async def translate_batch(self, texts, from_lang='en', to_lang='ar'):
    """Translate multiple texts in a single API call"""
    try:
      # Create numbered list of texts for batch translation
      numbered_texts = []
      for i, text in enumerate(texts, 1):
        numbered_texts.append(f"{i}. {text}")
      
      batch_text = "\n".join(numbered_texts)
      
      messages = [
        {
          "role": "user",
          "content": f"""Translate the following numbered list from {from_lang} to {to_lang}. 
Return the translations in the exact same numbered format, maintaining the same numbering.
Don't translate terms like 'Vibe Coding' or any terms like that that shouldn't be translated.
Return only the translated numbered list without any additional commentary:

{batch_text}"""
        }
      ]
      
      # Use the LLM to translate the batch
      translated_batch = self.llm.generate_response(
        messages=messages,
        model=os.getenv('OPENROUTER_LLM_MODEL')
      )
      
      # Parse the numbered response back into individual translations
      translated_lines = translated_batch.strip().split('\n')
      translations = []
      
      for line in translated_lines:
        if line.strip() and '. ' in line:
          # Remove the number prefix and get the translation
          translation = line.split('. ', 1)[1] if '. ' in line else line
          translations.append(translation.strip())
      
      # Ensure we have the same number of translations as inputs
      if len(translations) != len(texts):
        self.logger.warning(f"Expected {len(texts)} translations, got {len(translations)}. Falling back to individual translation.")
        # Fallback to individual translation if batch parsing fails
        individual_translations = []
        for text in texts:
          translation = await self.translate_text(text, from_lang, to_lang)
          individual_translations.append(translation)
        return individual_translations
      
      return translations
      
    except Exception as e:
      self.logger.error(f"Batch translation failed: {e}")
      # Fallback to individual translation
      individual_translations = []
      for text in texts:
        translation = await self.translate_text(text, from_lang, to_lang)
        individual_translations.append(translation)
      return individual_translations

  async def translate_srt(self, srt_path, from_language, target_language, output_path):
    try:
      subs = pysrt.open(srt_path)
      
      # Extract all subtitle texts
      subtitle_texts = [sub.text for sub in subs]
      
      # Define batch size (adjust based on model's context limit)
      batch_size = 30  # Process 30 subtitles at a time
      
      all_translations = []
      
      # Process subtitles in batches
      for i in range(0, len(subtitle_texts), batch_size):
        batch = subtitle_texts[i:i + batch_size]
        batch_translations = await self.translate_batch(batch, from_language, target_language)
        all_translations.extend(batch_translations)
        
        # Optional: Add small delay between batches to avoid rate limiting
        if i + batch_size < len(subtitle_texts):
          await asyncio.sleep(0.5)  # 500ms delay between batches
      
      # Apply translations back to subtitles
      for i, sub in enumerate(subs):
        if i < len(all_translations):
          sub.text = all_translations[i]
      
      subs.save(output_path, encoding='utf-8')
      
      self.logger.info(f"Translated {len(subs)} subtitles using {(len(subtitle_texts) + batch_size - 1) // batch_size} API requests")
      
      return output_path
    except Exception as e:
      self.logger.error(f"SRT translation failed: {e}")
      raise e
