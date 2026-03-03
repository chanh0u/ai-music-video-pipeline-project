export async function generate(story: string) {
  const form = new FormData();
  form.append("story", story);

  const res = await fetch("http://localhost:8000/generate", {
    method: "POST",
    body: form,
  });

  return res.json();
}