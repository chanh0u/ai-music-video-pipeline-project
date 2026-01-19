import { useState } from "react";
import { generate } from "../api";

export default function StoryInput() {
  const [story, setStory] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const submit = async () => {
    setLoading(true);
    const res = await generate(story);
    setResult(res);
    setLoading(false);
  };

  return (
    <div>
      <textarea
        className="w-full p-3 text-black"
        rows={6}
        placeholder="줄거리를 입력하세요"
        onChange={(e) => setStory(e.target.value)}
      />
      <button onClick={submit} className="mt-3 bg-pink-500 px-4 py-2">
        생성하기
      </button>

      {loading && <p>🎶 음악 생성 중...</p>}
      {result && (
        <div className="mt-4">
          <audio controls src={result.audio_url} />
          <video controls src={result.video_url} />
        </div>
      )}
    </div>
  );
}