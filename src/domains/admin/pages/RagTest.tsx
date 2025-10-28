import { useState } from 'react';

export default function RagTest() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);

  const run = async () => {
    // API 호출 연결
    setAnswer(`(샘플 응답) "${query}" 에 대한 RAG 결과`);
  };

  return (
    <section className="space-y-4">
      <h1 className="text-xl font-semibold">RAG 테스트</h1>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-md border px-3 py-2"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="질문을 입력하세요"
        />
        <button className="rounded-md bg-gray-900 px-4 py-2 text-white" onClick={run}>
          실행
        </button>
      </div>
      {answer && <div className="rounded-md border bg-white p-4">{answer}</div>}
    </section>
  );
}
