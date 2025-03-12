import moviepy.editor as mp
import openai
import tempfile
import os
import json
import time
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def process_video_segments(video_path, segment_duration=30):
    video = mp.VideoFileClip(video_path)
    duration = video.duration
    segments = []
    for start in range(0, int(duration), segment_duration):
        end = min(start + segment_duration, duration)
        segments.append((start, end))
    return segments, duration, video

def extract_audio(video_clip, output_path):
    try:
        video_clip.audio.write_audiofile(
            output_path,
            codec='mp3',  # Changed to mp3 format
            ffmpeg_params=["-ac", "1", "-ar", "16000"],
            verbose=False,
            logger=None
        )
        return True
    except:
        return False

def extract_reel(video_path, start_time, end_time, output_path):
    video = mp.VideoFileClip(video_path)
    try:
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")
        if end_time > video.duration:
            end_time = video.duration
        reel = video.subclip(start_time, end_time)
        reel.write_videofile(output_path, codec="libx264", audio_codec="aac")
        return output_path
    finally:
        video.close()

def generate_thumbnail(video_path, timestamp, output_path):
    video = mp.VideoFileClip(video_path)
    try:
        if timestamp > video.duration:
            timestamp = video.duration - 1
        thumbnail = video.get_frame(timestamp)
        mp.ImageClip(thumbnail).save_frame(output_path)
        return output_path
    finally:
        video.close()

def make_openai_request(func, *args, max_retries=3, delay=1, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except openai.error.APIError:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (attempt + 1))

def generate_caption(video_path, prompt_overrides=None):
    segments, duration, video = process_video_segments(video_path)
    transcripts = []
    try:
        for start, end in segments:
            segment = video.subclip(start, end)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                if extract_audio(segment, temp_audio.name):
                    with open(temp_audio.name, "rb") as audio_file:
                        result = make_openai_request(
                            openai.Audio.transcribe,
                            "whisper-1",
                            file=audio_file
                        )
                        transcripts.append(result["text"])
                os.unlink(temp_audio.name)
            segment.close()

        if not transcripts:
            return "No audio content detected in the video."

        full_transcript = " ".join(transcripts)
        base_prompt = "Generate a concise and engaging social media caption for this video transcript"
        prompt = f"{base_prompt}: {full_transcript}" if not prompt_overrides else f"{prompt_overrides}: {full_transcript}"
        
        response = make_openai_request(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates social media captions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    finally:
        video.close()

def create_multiple_highlight_reels(video_path, output_dir, topic=None, target_duration=60, num_reels=5):
    segments, duration, video = process_video_segments(video_path)
    transcripts = []
    try:
        for start, end in segments:
            segment = video.subclip(start, end)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                if extract_audio(segment, temp_audio.name):
                    with open(temp_audio.name, "rb") as audio_file:
                        result = make_openai_request(
                            openai.Audio.transcribe,
                            "whisper-1",
                            file=audio_file
                        )
                        transcripts.append((start, result["text"]))
                os.unlink(temp_audio.name)
            segment.close()

        combined_transcript = " ".join([t[1] for t in transcripts])
        output_paths = []

        for i in range(num_reels):
            system_prompt = """You are a developer assistant where you only provide timestamps in this exact format: [[start1, end1], [start2, end2]].
Given the transcript segments, generate a list of highlights with start and end times for the video using multiple segments.

Constraints:
•⁠  ⁠The highlights should be a direct part of the video and not out of context
•⁠  ⁠The highlights should be interesting and clippable, providing value to the viewer
•⁠  ⁠The highlights should be just the right length to convey the information
•⁠  ⁠The highlights should include more than one segment for context and continuity
•⁠  ⁠The highlights should not cut off mid-sentence
•⁠  ⁠The highlights should be based on segment relevance
•⁠  ⁠Each segment should be scored out of 100 based on relevance
•⁠  ⁠When a specific topic is provided, extract the complete segment discussing that topic without breaks
•⁠  ⁠Topic-specific clips should maintain full context and natural flow of conversation
•⁠  ⁠Include surrounding context if the topic discussion extends beyond immediate mentions

Return ONLY the timestamp arrays like this:
[[0, 15], [30, 45], [50, 65]]"""

            
            topic_instruction = ""
            if topic:
                topic_instruction = f"Focus specifically on segments discussing {topic}. Only select parts relevant to {topic}."
            
            user_prompt = f"""Create a {target_duration} second highlight reel (variation {i+1}).
            {topic_instruction}
            Return timestamps in seconds as a JSON array. Make this selection different from other variations.
            Duration: {duration} seconds
            Transcript: {combined_transcript}"""
            
            response = make_openai_request(
                openai.ChatCompletion.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9
            )
            
            try:
                content = response.choices[0].message.content.strip()
                timestamps = json.loads(content)
            except:
                timestamps = [[i * (duration/num_reels), min((i+1) * (duration/num_reels), duration)]]
            
            clips = []
            total_duration = 0
            
            for start, end in timestamps:
                if start < duration and end <= duration and total_duration < target_duration:
                    clip = video.subclip(start, end)
                    clips.append(clip)
                    total_duration += end - start
            
            output_path = os.path.join(output_dir, f"highlight_reel_{topic}_{i+1}.mp4" if topic else f"highlight_reel_{i+1}.mp4")
            
            if clips:
                final_video = mp.concatenate_videoclips(clips)
                final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
            else:
                video.subclip(0, min(target_duration, duration)).write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            output_paths.append(output_path)
            
        return output_paths
    finally:
        video.close()

