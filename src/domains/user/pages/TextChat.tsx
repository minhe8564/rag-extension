import { useState } from 'react';

type Msg = { role: 'user' | 'assistant'; content: string };

export default function TextChat() {
  const [input, setInput] = useState('');
  const [list, setList] = useState<Msg[]>([]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: Msg = { role: 'user', content: input };
    setList(prev => [...prev, userMsg]);
    setInput('');
    // API 호출
    const assistant: Msg = { role: 'assistant', content: `(${userMsg.content}) 에 대한 응답 예시` };
    setList(prev => [...prev, assistant]);
  };

  return (
    <section className="grid grid-rows-[1fr_auto] gap-4">
      <div className="space-y-2">
        {list.length === 0 && (
          <div className="rounded-md border bg-white p-4 text-sm text-gray-500">
            메시지를 입력해 대화를 시작하세요.
          </div>
        )}
        {list.map((m, i) => (
          <div
            key={i}
            className={
              'max-w-[80%] rounded-md border p-3 ' +
              (m.role === 'user' ? 'ml-auto bg-gray-900 text-white' : 'bg-white')
            }
          >
            <div className="text-xs opacity-70">{m.role}</div>
            <div>{m.content}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-md border px-3 py-2"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="메시지를 입력하세요"
          onKeyDown={e => e.key === 'Enter' && send()}
        />
        <button className="rounded-md bg-gray-900 px-4 py-2 text-white" onClick={send}>
          전송
        </button>
      </div>
    </section>
  );
}
