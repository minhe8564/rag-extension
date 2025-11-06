import { useEffect, useRef, useState } from 'react';
import ChatInput from '@/shared/components/chat/ChatInput';
import { Pencil, ThumbsUp, ThumbsDown, Copy } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import { toast } from 'react-toastify';

type Msg = { role: 'user' | 'assistant'; content: string; model: string };

export default function TextChat() {
  const [list, setList] = useState<Msg[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleSend = async (msg: string) => {
    // 사용자 메시지 추가
    const userMsg: Msg = { role: 'user', content: msg, model: 'gpt-4.0' };
    setList((prev) => [...prev, userMsg]);

    // 실제 API 호출
    const assistant: Msg = {
      role: 'assistant',
      content: `(${msg}) 에 대한 응답 예시`,
      model: 'gpt-4.0',
    };
    setList((prev) => [...prev, assistant]);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [list]);

  const hasMessages = list.length > 0;

  return (
    <>
      <section className="h-[calc(100vh-62px)] flex flex-col">
        {hasMessages ? (
          <>
            <div className="flex-1 min-h-0 w-full flex justify-center overflow-y-scroll no-scrollbar">
              <div className="w-full max-w-[75%] space-y-6 px-12 py-4">
                {list.map((m, i) => {
                  const isUser = m.role === 'user';

                  return (
                    <div
                      key={i}
                      className={
                        'w-fit max-w-[75%] rounded-md border p-3 relative group break-words ' +
                        (isUser ? 'ml-auto bg-[var(--color-hebees-bg)] text-black' : 'bg-white')
                      }
                    >
                      <div className="whitespace-pre-wrap">{m.content}</div>

                      {!isUser && m.model && (
                        <div className="text-[10px] text-gray-400 mt-1">{m.model}</div>
                      )}

                      <div
                        className={`
          absolute flex gap-2 items-center 
          ${isUser ? 'right-2' : 'left-2'} 
          bottom-[-30px] opacity-0 group-hover:opacity-100 
          transition-opacity duration-200
        `}
                      >
                        {isUser ? (
                          <Tooltip content="다시 입력하기" side="bottom">
                            <button
                              onClick={() => console.log('edit:', m.content)}
                              className="p-1 rounded hover:bg-gray-100"
                            >
                              <Pencil size={14} className="text-gray-500" />
                            </button>
                          </Tooltip>
                        ) : (
                          <>
                            <Tooltip content="좋은 응답" side="bottom">
                              <button
                                onClick={() => console.log('thumbs up', m.content)}
                                className="p-1 rounded hover:bg-gray-100"
                              >
                                <ThumbsUp size={14} className="text-gray-500" />
                              </button>
                            </Tooltip>

                            <Tooltip content="별로인 응답" side="bottom">
                              <button
                                onClick={() => console.log('thumbs down', m.content)}
                                className="p-1 rounded hover:bg-gray-100"
                              >
                                <ThumbsDown size={14} className="text-gray-500" />
                              </button>
                            </Tooltip>

                            <Tooltip content="복사하기" side="bottom">
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(m.content);
                                  toast.success('클립보드에 복사되었습니다.');
                                }}
                                className="p-1 rounded hover:bg-gray-100"
                              >
                                <Copy size={14} className="text-gray-500" />
                              </button>
                            </Tooltip>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={bottomRef} />
              </div>
            </div>

            <div className="sticky bottom-0 shrink-0 w-full flex justify-center pb-5 bg-white">
              <div className="w-full max-w-[75%]">
                <ChatInput onSend={handleSend} variant="hebees" />
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 min-h-[calc(100vh-62px)] flex items-center justify-center px-4">
            <div className="w-full max-w-[75%] flex flex-col items-center gap-6 text-center">
              <ChatInput onSend={handleSend} variant="hebees" />
            </div>
          </div>
        )}
      </section>
    </>
  );
}
