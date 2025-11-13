import { useEffect, useRef, useState } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import ChatInput from '@/shared/components/chat/ChatInput';
import ChatMessageItem from '@/shared/components/chat/ChatMessageItem';
import ScrollToBottomButton from '@/shared/components/chat/ScrollToBottomButton';
// import { getSession, getMessages, sendMessage } from '@/shared/api/chat.api';
import { getSession, getMessages } from '@/shared/api/chat.api';
import type { UiMsg, UiRole } from '@/shared/components/chat/ChatMessageItem';
import type {
  ChatRole,
  MessageItem,
  MessagePage,
  // SendMessageRequest,
  // SendMessageResult,
} from '@/shared/types/chat.types';
import {
  useDerivedSessionNo,
  useEnsureSession,
  useThinkingTicker,
} from '@/domains/user/hooks/useChatHelpers';
import { useChatModelStore } from '@/shared/store/useChatModelStore';
import type { RagQueryProcessResult } from '@/shared/types/chat.rag.types';
import { postRagQuery } from '@/shared/api/chat.rag.api';

const mapRole = (r: ChatRole): UiRole => (r === 'human' ? 'user' : r === 'ai' ? 'assistant' : r);

export default function TextChat() {
  const { sessionNo: paramsSessionNo } = useParams<{ sessionNo: string }>();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const derivedSessionNo = useDerivedSessionNo(location, searchParams, paramsSessionNo);

  const [currentSessionNo, setCurrentSessionNo] = useState<string | null>(derivedSessionNo);
  const [list, setList] = useState<UiMsg[]>([]);
  const [awaitingAssistant, setAwaitingAssistant] = useState<boolean>(false);

  const [initialLoading, setInitialLoading] = useState<boolean>(Boolean(derivedSessionNo));
  const [llmNo, setLlmNo] = useState<string | null>(null);

  const { selectedModel, setSelectedModel } = useChatModelStore();

  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const forceScrollRef = useRef<boolean>(false);

  const ensureSession = useEnsureSession(setCurrentSessionNo);
  const sessionPromiseRef = useRef<Promise<string> | null>(null);

  const getOrCreateSessionNo = async (llmName: string, firstMsg: string): Promise<string> => {
    if (currentSessionNo) return currentSessionNo;

    if (!sessionPromiseRef.current) {
      sessionPromiseRef.current = ensureSession({ llm: llmName, query: firstMsg })
        .then((sn) => {
          setCurrentSessionNo(sn);
          return sn;
        })
        .finally(() => {
          sessionPromiseRef.current = null;
        });
    }
    return sessionPromiseRef.current;
  };

  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (!derivedSessionNo) {
        if (!selectedModel) setSelectedModel('Qwen3-vl:8B');
        setInitialLoading(false);
        return;
      }

      setInitialLoading(true);
      setCurrentSessionNo(derivedSessionNo);

      try {
        const [resMsgs, resSess] = await Promise.all([
          getMessages(derivedSessionNo),
          getSession(derivedSessionNo),
        ]);

        const page = resMsgs.data.result as MessagePage;
        const sessionInfo = resSess.data.result as { llmNo?: string; llmName?: string } | undefined;

        const llmName: string = sessionInfo?.llmName ?? selectedModel ?? 'Qwen3-vl:8B';
        setSelectedModel(llmName);
        if (sessionInfo?.llmNo) {
          setLlmNo(sessionInfo.llmNo);
        }

        const mapped: UiMsg[] =
          (page.data ?? []).map(
            (m: MessageItem): UiMsg => ({
              role: mapRole(m.role),
              content: m.content,
              createdAt: m.createdAt,
              messageNo: m.messageNo,
              referencedDocuments: m.referencedDocuments,
            })
          ) ?? [];

        if (!cancelled) {
          setList(mapped);
          requestAnimationFrame(() => bottomRef.current?.scrollIntoView());
        }
      } catch {
        if (!cancelled) setList([]);
      } finally {
        if (!cancelled) setInitialLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [derivedSessionNo, setSelectedModel]);

  const isAtBottom = (): boolean => {
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

  const handleSend = async (msg: string): Promise<void> => {
    forceScrollRef.current = true;
    setAwaitingAssistant(true);

    setList((prev: UiMsg[]) => [
      ...prev,
      { role: 'user', content: msg },
      { role: 'assistant', content: '', messageNo: '__pending__' },
    ]);

    try {
      const llmName: string = selectedModel ?? 'Qwen3-vl:8B';
      const sessionNo: string = await getOrCreateSessionNo(llmName, msg);

      // const body: SendMessageRequest = { content: msg, model: llmName };
      // const res = await sendMessage(sessionNo, body);
      // const result = res.data.result as SendMessageResult;
      if (!llmNo) {
        throw new Error('LLM 정보가 없습니다. 세션 정보를 다시 불러와 주세요.');
      }
      const res = await postRagQuery({
        llmNo,
        sessionNo,
        query: msg,
      });
      const result = res.data.result as RagQueryProcessResult;

      forceScrollRef.current = true;
      setList((prev: UiMsg[]) =>
        prev.map(
          (m: UiMsg): UiMsg =>
            m.messageNo === '__pending__'
              ? {
                  role: 'assistant',
                  content: result.content ?? '(응답이 없습니다)',
                  // createdAt: result.timestamp,
                  createdAt: result.createdAt,
                  messageNo: result.messageNo,
                }
              : m
        )
      );
    } catch {
      setList((prev: UiMsg[]) => prev.filter((m: UiMsg) => m.messageNo !== '__pending__'));
    } finally {
      setAwaitingAssistant(false);
    }
  };

  const thinkingSubtitle = useThinkingTicker(awaitingAssistant);

  if (initialLoading) {
    return (
      <section className="flex flex-col min-h-[calc(100vh-82px)] h-full">
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="flex flex-col items-center gap-3 text-gray-500">
            <div className="w-8 h-8 rounded-full border-2 border-gray-300 border-t-gray-600 animate-spin" />
            <div className="text-sm">채팅 불러오는 중…</div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="flex flex-col min-h-[calc(100vh-82px)] h-full">
      {list.length > 0 ? (
        <>
          <div
            ref={scrollRef}
            className="relative flex-1 min-h-0 w-full flex justify-center overflow-y-auto no-scrollbar"
          >
            <div className="w-full max-w-[75%] space-y-10 px-12 py-4">
              {list.map((m: UiMsg, i: number) => (
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
                  brand="hebees"
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
              <ChatInput onSend={handleSend} variant="hebees" />
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="w-full max-w-[75%] flex flex-col items-center gap-6 text-center">
            <ChatInput onSend={handleSend} variant="hebees" />
          </div>
        </div>
      )}
    </section>
  );
}
