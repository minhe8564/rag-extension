import { useState } from 'react';

export default function RagSettings() {
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.4);

  const save = async () => {
    // 설정 저장 API
    console.log('save settings', { topK, threshold });
    alert('저장되었습니다.');
  };

  return (
    <section className="space-y-4">
      <h1 className="text-xl font-semibold">RAG 설정</h1>
      <div className="grid max-w-xl gap-4 rounded-md border bg-white p-4">
        <label className="grid grid-cols-[140px_1fr] items-center gap-3">
          <span className="text-sm text-gray-600">Top K</span>
          <input
            type="number"
            min={1}
            className="rounded-md border px-3 py-2"
            value={topK}
            onChange={e => setTopK(Number(e.target.value))}
          />
        </label>
        <label className="grid grid-cols-[140px_1fr] items-center gap-3">
          <span className="text-sm text-gray-600">Score Threshold</span>
          <input
            type="number"
            step="0.01"
            min={0}
            max={1}
            className="rounded-md border px-3 py-2"
            value={threshold}
            onChange={e => setThreshold(Number(e.target.value))}
          />
        </label>
        <div>
          <button className="rounded-md bg-gray-900 px-4 py-2 text-white" onClick={save}>
            저장
          </button>
        </div>
      </div>
    </section>
  );
}
