import React, { useState } from "react";

function App() {
  const [story, setStory] = useState("");
  const [genre, setGenre] = useState("ballad");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const generate = async () => {
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("story", story);
    formData.append("genre", genre);

    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>🎵 AI Story → Music</h1>

      <textarea
        rows={6}
        placeholder="줄거리를 입력하세요"
        value={story}
        onChange={(e) => setStory(e.target.value)}
        style={{ width: "100%", padding: 10 }}
      />

      <div style={{ marginTop: 10 }}>
        <select value={genre} onChange={(e) => setGenre(e.target.value)}>
          <option value="ballad">Ballad</option>
          <option value="hiphop">Hip-hop</option>
          <option value="edm">EDM</option>
        </select>

        <button
          onClick={generate}
          disabled={loading}
          style={{ marginLeft: 10 }}
        >
          {loading ? "생성 중..." : "🎶 생성"}
        </button>
      </div>

      {result && (
        <div style={{ marginTop: 30 }}>
          <p>🎭 Emotion: {result.emotion}</p>

          <audio controls src={result.audio_url} />
          <br />
          <video
            controls
            width="100%"
            src={result.video_url}
            style={{ marginTop: 10 }}
          />
        </div>
      )}
    </div>
  );
}

export default App;