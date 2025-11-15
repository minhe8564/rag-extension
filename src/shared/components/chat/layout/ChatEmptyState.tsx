import { useEffect, useState } from 'react';

interface ChatEmptyStateProps {
  onSelectPrompt?: (prompt: string) => void | Promise<void>;
}

function useTypingEffect(text: string | undefined, speed = 120) {
  const safeText = text ?? '';
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!safeText) {
      setIndex(0);
      return;
    }

    setIndex(0);

    const interval = setInterval(() => {
      setIndex((prev) => {
        if (prev >= safeText.length) {
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, speed);

    return () => {
      clearInterval(interval);
    };
  }, [safeText, speed]);

  return safeText.slice(0, index);
}

function TypingEffect({ text, speed = 120 }: { text: string | undefined; speed?: number }) {
  const displayed = useTypingEffect(text, speed);

  if (!text) {
    return (
      <span className="whitespace-pre">
        <span
          className="inline-block w-1 h-5 animate-pulse"
          style={{
            background: 'linear-gradient(90deg, #BE7DB1 10%, #81BAFF 100%)',
          }}
        />
      </span>
    );
  }

  return (
    <span className="whitespace-pre">
      {displayed}
      <span
        className="inline-block w-1 h-7 animate-pulse ml-2 my-1 align-top"
        style={{
          background: 'linear-gradient(90deg, #BE7DB1 10%, #81BAFF 100%)',
        }}
      />
    </span>
  );
}

const SUGGESTED_PROMPTS = [
  '업로드한 문서 요약해줘',
  '문서 기반으로 나에게 맞는 안경 스타일 추천해줘',
  '문서에서 제품 스펙 비교해서 핵심만 알려줘',
  '문서 기반으로 사용자에게 필요한 옵션 정리해줘',
  '업로드한 문서의 핵심 개념만 정리해줘',
];

function ChatEmptyState({ onSelectPrompt }: ChatEmptyStateProps) {
  const handlePromptClick = (prompt: string) => {
    if (!onSelectPrompt) return;
    void onSelectPrompt(prompt);
  };

  return (
    <div className="w-full flex flex-col items-center gap-10 mb-20">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white/70 px-3 py-1 text-xs font-medium text-gray-600 shadow-sm">
          <span className="relative mr-1 inline-flex h-2.5 w-2.5 items-center justify-center">
            <span
              className="absolute inline-flex h-full w-full rounded-full opacity-70 animate-ping"
              style={{
                background: 'linear-gradient(90deg, #BE7DB1 10%, #81BAFF 100%)',
              }}
            ></span>

            <span
              className="relative inline-flex h-2.5 w-2.5 rounded-full animate-pulse"
              style={{
                background: 'linear-gradient(90deg, #BE7DB1 10%, #81BAFF 100%)',
              }}
            ></span>
          </span>
          HEBEES RAG 챗봇
        </div>

        <h2
          className="text-4xl font-bold bg-clip-text text-transparent"
          style={{
            backgroundImage: 'linear-gradient(90deg, #BE7DB1 10%, #81BAFF 100%)',
          }}
        >
          <TypingEffect text="문서를 기반으로 어떤 답변이 필요하신가요?" speed={120} />
        </h2>
      </div>

      <div className="w-full rounded-2xl border border-gray-100 bg-white p-4 shadow-sm">
        <p className="mb-6 text-sm font-medium text-gray-500">💡 이렇게 질문해볼 수 있어요</p>

        <div className="flex flex-wrap gap-2 justify-center">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => handlePromptClick(prompt)}
              className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3.5 py-1.5 text-[11px] text-gray-700 hover:bg-gray-100 hover:border-gray-300 transition-colors"
            >
              <span className="text-xs inline-block h-1.5 w-1.5 rounded-full bg-gray-400" />
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* <p className="text-[11px] text-gray-400 text-center">
        먼저 문서를 업로드하면 더 정확한 답변을 받을 수 있습니다.
        <br />
        Enter = 전송 · Shift + Enter = 줄바꿈
      </p> */}
    </div>
  );
}

export default ChatEmptyState;
