import requests
import argparse
import os
import sys
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"

def check_server_health() -> bool:
    try:
        response = requests.get(f"{BASE_URL}/health/")
        return response.status_code == 200
    except requests.ConnectionError:
        return False

def process_video(
    video_path: str,
    reel_start: Optional[float] = None,
    reel_end: Optional[float] = None,
    thumbnail_time: Optional[float] = None,
    caption_prompt: Optional[str] = None,
    highlight_duration: Optional[float] = None,
    num_reels: Optional[int] = None
) -> None:
    """Processes a video using the FastAPI endpoints."""
    
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at {video_path}")
        sys.exit(1)
        
    if not check_server_health():
        print("❌ Error: Server is not running or not accessible")
        sys.exit(1)

    with open(video_path, "rb") as file:
        files = {"file": file}

        # Generate multiple highlight reels
        if highlight_duration is not None:
            print("📽️ Generating highlight reels...")
            data = {
                "target_duration": highlight_duration,
                "num_reels": num_reels or 5
            }
            response = requests.post(f"{BASE_URL}/highlight-reels/", files=files, data=data)
            if response.status_code == 200:
                with open("highlight_reels.zip", "wb") as f:
                    f.write(response.content)
                print("✅ Highlight reels created: highlight_reels.zip")
            else:
                print(f"❌ Failed to create highlight reels: {response.text}")

        # Original reel creation
        if reel_start is not None and reel_end is not None:
            print("🎬 Creating reel...")
            reel_data = {"start_time": reel_start, "end_time": reel_end}
            response = requests.post(f"{BASE_URL}/reel/", files=files, data=reel_data)
            if response.status_code == 200:
                with open("output_reel.mp4", "wb") as f:
                    f.write(response.content)
                print("✅ Reel created: output_reel.mp4")
            else:
                print(f"❌ Failed to create reel: {response.text}")

        # Thumbnail generation
        if thumbnail_time is not None:
            print("🖼️ Generating thumbnail...")
            thumbnail_data = {"timestamp": thumbnail_time}
            response = requests.post(f"{BASE_URL}/thumbnail/", files=files, data=thumbnail_data)
            if response.status_code == 200:
                with open("output_thumbnail.jpg", "wb") as f:
                    f.write(response.content)
                print("✅ Thumbnail created: output_thumbnail.jpg")
            else:
                print(f"❌ Failed to create thumbnail: {response.text}")

        # Caption generation
        if caption_prompt is not None:
            print("📝 Generating caption...")
            caption_data = {"prompt_overrides": caption_prompt}
            response = requests.post(f"{BASE_URL}/caption/", files=files, data=caption_data)
            if response.status_code == 200:
                print(f"✅ Caption: {response.json()['caption']}")
            else:
                print(f"❌ Failed to generate caption: {response.text}")

def main():
    parser = argparse.ArgumentParser(
        description="Process video for social media.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("video_path", help="Path to the video file")
    parser.add_argument("--reel_start", type=float, help="Start time for reel (seconds)")
    parser.add_argument("--reel_end", type=float, help="End time for reel (seconds)")
    parser.add_argument("--thumbnail_time", type=float, help="Timestamp for thumbnail (seconds)")
    parser.add_argument("--caption_prompt", type=str, help="Custom caption prompt")
    parser.add_argument("--highlight_duration", type=float, help="Duration for each highlight reel (seconds)")
    parser.add_argument("--num_reels", type=int, default=5, help="Number of highlight reels to generate")

    args = parser.parse_args()

    try:
        process_video(
            args.video_path,
            args.reel_start,
            args.reel_end,
            args.thumbnail_time,
            args.caption_prompt,
            args.highlight_duration,
            args.num_reels
        )
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
