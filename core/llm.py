import os
from openai import OpenAI

class LLM:
  def __init__(self):
    self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.getenv('OPENROUTER_API_KEY'))

  def generate_response(self, messages, model):
    response = self.client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
  