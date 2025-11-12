import { useEffect, useRef, useState } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import ChatInput from '@/shared/components/chat/ChatInput';
import ChatMessageItem from '@/shared/components/chat/ChatMessageItem';
import ScrollToBottomButton from '@/shared/components/chat/ScrollToBottomButton';
import { getSession, getMessages, sendMessage } from '@/shared/api/chat.api';
import type { UiMsg, UiRole } from '@/shared/components/chat/ChatMessageItem';
import type {
  ChatRole,
  MessageItem,
  MessagePage,
  SendMessageRequest,
  SendMessageResult,
} from '@/shared/types/chat.types';
import {
  useDerivedSessionNo,
  useEnsureSession,
  useThinkingTicker,
} from '@/domains/user/hooks/useChatHelpers';

const DEFAULT_LLM = 'qwen3-vl:8b';
const NAME_TO_ID: Record<string, string> = {
  'Qwen3-vl:8B': 'qwen3-vl:8b',
  'GPT-4o': 'gpt-4o',
  'Gemini 2.5-Flash': 'gemini 2.5-flash',
  'Claude Sonnet 4': 'claude-sonnet 4',
};
const mapNameToId = (name?: string) => (name ? NAME_TO_ID[name] : undefined);

const mapRole = (r: ChatRole): UiRole => (r === 'human' ? 'user' : r === 'ai' ? 'assistant' : r);

export default function TextChat() {
  const { sessionNo: paramsSessionNo } = useParams<{ sessionNo: string }>();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const derivedSessionNo = useDerivedSessionNo(location, searchParams, paramsSessionNo);

  const [currentSessionNo, setCurrentSessionNo] = useState<string | null>(derivedSessionNo);
  const [list, setList] = useState<UiMsg[]>([]);
  const [awaitingAssistant, setAwaitingAssistant] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const forceScrollRef = useRef(false);

  const ensureSession = useEnsureSession(setCurrentSessionNo);

  useEffect(() => {
    (async () => {
      if (!derivedSessionNo) {
        if (!model) setModel(DEFAULT_LLM);
        return;
      }

      setCurrentSessionNo(derivedSessionNo);

      const resMsgs = await getMessages(derivedSessionNo);
      const page: MessagePage = resMsgs.data.result;

      const resSess = await getSession(derivedSessionNo);
      const sessionInfo = resSess.data.result as { llm?: string; llmName?: string } | undefined;

      const llmId = sessionInfo?.llm || mapNameToId(sessionInfo?.llmName) || DEFAULT_LLM;
      setModel(llmId);

      const mapped: UiMsg[] =
        page.data?.map((m: MessageItem) => ({
          role: mapRole(m.role),
          content: m.content,
          createdAt: m.createdAt,
          messageNo: m.messageNo,
          referencedDocuments: m.referencedDocuments,
        })) ?? [];

      setList(mapped);
      requestAnimationFrame(() => bottomRef.current?.scrollIntoView());
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [derivedSessionNo, setModel]);

  const isAtBottom = () => {
    const el = scrollRef.current;
    return !el || el.scrollTop + el.clientHeight >= el.scrollHeight - 50;
  };

  useEffect(() => {
    if (forceScrollRef.current) {
      forceScrollRef.current = false;
      requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }));
      return;
    }
    if (isAtBottom()) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [list.length]);

  const handleSend = async (msg: string) => {
    forceScrollRef.current = true;
    setAwaitingAssistant(true);

    setList((prev) => [
      ...prev,
      { role: 'user', content: msg },
      { role: 'assistant', content: '', messageNo: '__pending__' },
    ]);

    try {
      const llmId = model || DEFAULT_LLM;
      const sessionNo = await ensureSession({ llm: llmId, query: msg });

      const body: SendMessageRequest = { content: msg, model: llmId };
      const res = await sendMessage(sessionNo, body);
      const result: SendMessageResult = res.data.result;

      forceScrollRef.current = true;
      setList((prev) =>
        prev.map((m) =>
          m.messageNo === '__pending__'
            ? {
                role: 'assistant',
                content: result.content ?? '(응답이 없습니다)',
                createdAt: result.timestamp,
              }
            : m
        )
      );
    } catch {
      setList((prev) => prev.filter((m) => m.messageNo !== '__pending__'));
    } finally {
      setAwaitingAssistant(false);
    }
  };

  const thinkingSubtitle = useThinkingTicker(awaitingAssistant);

  return (
    <section className="flex flex-col min-h-[calc(100vh-82px)] h-full">
      {list.length > 0 ? (
        <>
          <div
            ref={scrollRef}
            className="relative flex-1 min-h-0 w-full flex justify-center overflow-y-auto no-scrollbar"
          >
            <div className="w-full max-w-[75%] space-y-10 px-12 py-4">
              {list.map((m, i) => (
                <ChatMessageItem
                  key={`${m.messageNo ?? 'pending'}-${i}`}
                  msg={m}
                  index={i}
                  currentSessionNo={currentSessionNo}
                  isEditing={false}
                  editingDraft=""
                  onStartReask={() => {}}
                  onCancelReask={() => {}}
                  onSubmitReask={() => {}}
                  isPendingAssistant={awaitingAssistant && m.role === 'assistant' && !m.content}
                  pendingSubtitle={thinkingSubtitle}
                  brand="retina"
                />
              ))}
              <div ref={bottomRef} />
            </div>
          </div>

          <div className="sticky bottom-0 w-full flex flex-col items-center">
            <div className="relative w-full flex justify-center mb-4">
              <ScrollToBottomButton
                containerRef={scrollRef}
                watch={list.length}
                className="absolute bottom-0"
              />
            </div>
            <div className="w-full max-w-[75%] pb-6 bg-white">
              <ChatInput onSend={handleSend} variant="retina" />
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-[75%] flex flex-col items-center gap-6 text-center">
            <ChatInput onSend={handleSend} variant="retina" />
          </div>
        </div>
      )}
    </section>
  );
}
