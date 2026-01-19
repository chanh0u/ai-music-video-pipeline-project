# services/music.py
def generate_music(lyrics, genre, voice):
    path = "/tmp/music.mp3"
    # 실제로는 MusicLM / Riffusion API 호출
    with open(path, "wb") as f:
        f.write(b"FAKE_MP3_DATA")
    return path