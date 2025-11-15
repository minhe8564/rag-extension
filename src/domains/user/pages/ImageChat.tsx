import { useState } from 'react';

export default function ImageChat() {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');

  const send = async () => {
    if (!file && !prompt.trim()) return;
    // 업로드 + 프롬프트 전송 API
    alert('샘플: 이미지/프롬프트 전송됨');
  };

  return (
    <section className="space-y-4">
      <h1 className="text-xl font-semibold">이미지 채팅</h1>
      <div className="rounded-md border bg-white p-4">
        <div className="mb-3">
          <input
            type="file"
            accept="image/*"
            onChange={e => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <textarea
          className="h-24 w-full resize-none rounded-md border px-3 py-2"
          placeholder="프롬프트를 입력하세요"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
        />
        <div className="mt-3">
          <button className="rounded-md bg-gray-900 px-4 py-2 text-white" onClick={send}>
            전송
          </button>
        </div>
      </div>
    </section>
  );
}
