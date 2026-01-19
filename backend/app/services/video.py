# services/video.py
def generate_video(summary, audio_path):
    path = "/tmp/video.mp4"
    # Runway / SD API 대체
    with open(path, "wb") as f:
        f.write(b"FAKE_MP4_DATA")
    return path