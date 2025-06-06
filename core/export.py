
import os

class Export:
  def save_to_file(self, result, file_path):
    with open(file_path, "w") as f:
      f.write(result)

  def generate_srt(self, result):
    def format_timestamp(seconds):
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    srt_lines = []
    for i, segment in enumerate(result['segments']):
        start_time = format_timestamp(segment['start'])
        end_time = format_timestamp(segment['end'])
        
        # SRT format: sequence number, timestamp, text, blank line
        srt_lines.append(f"{i + 1}")  # Sequence numbers start from 1
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(segment['text'].strip())
        srt_lines.append("")  # Blank line separator
    
    # Remove the last blank line to avoid extra newline at end
    if srt_lines and srt_lines[-1] == "":
        srt_lines.pop()
    
    output = "\n".join(srt_lines)
    
    # Use absolute path to avoid path resolution issues
    srt_path = os.path.abspath("temp/result.srt")
    self.save_to_file(output, srt_path)
    
    return srt_path
  
  def compile_srt_to_ass(self, srt_path):
    pass