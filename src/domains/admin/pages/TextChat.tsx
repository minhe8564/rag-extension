import { useEffect, useRef, useState } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import ChatInput from '@/shared/components/chat/ChatInput';
import ChatMessageItem from '@/shared/components/chat/ChatMessageItem';
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
import { useChatModelStore } from '@/shared/store/useChatModelStore';
import type { RagQueryProcessResult } from '@/shared/types/chat.rag.types';
import { postRagQuery } from '@/shared/api/chat.rag.api';
import { toast } from 'react-toastify';
import ChatEmptyState from '@/shared/components/chat/ChatEmptyState';

const mapRole = (r: ChatRole): UiRole => (r === 'human' ? 'user' : r === 'ai' ? 'assistant' : r);

type ChatMode = 'llm' | 'rag';

export default function TextChat() {
  const { sessionNo: paramsSessionNo } = useParams<{ sessionNo: string }>();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const derivedSessionNo = useDerivedSessionNo(location, searchParams, paramsSessionNo, 'user');

  const [currentSessionNo, setCurrentSessionNo] = useState<string | null>(derivedSessionNo);
  const [list, setList] = useState<UiMsg[]>([]);
  const [awaitingAssistant, setAwaitingAssistant] = useState(false);
  const [initialLoading, setInitialLoading] = useState<boolean>(Boolean(derivedSessionNo));

  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const forceScrollRef = useRef(false);

  const ensureSession = useEnsureSession(setCurrentSessionNo, 'user');
  const sessionPromiseRef = useRef<Promise<string> | null>(null);

  const { selectedModel, selectedLlmNo, setSelectedModel } = useChatModelStore();
  const [llmNo, setLlmNo] = useState<string | null>(null);

  const [historyCursor, setHistoryCursor] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [hasMoreHistory, setHasMoreHistory] = useState(true);

  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editingDraft, setEditingDraft] = useState<string>('');
  const [mode, setMode] = useState<ChatMode>('llm');

  const startReask = (idx: number, content: string) => {
    setEditingIdx(idx);
    setEditingDraft(content);
  };
  const cancelReask = () => {
    setEditingIdx(null);
    setEditingDraft('');
  };
  const submitReask = async (value: string) => {
    await handleSend(value);
    setEditingIdx(null);
    setEditingDraft('');
    toast.success('수정된 질문으로 다시 보냈습니다.');
  };

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
        if (!selectedModel) setSelectedModel('Qwen3-vl:8B', selectedLlmNo);
        setInitialLoading(false);
        return;
      }

      setInitialLoading(true);
      setCurrentSessionNo(derivedSessionNo);
      setHistoryCursor(null);
      setHasMoreHistory(true);
      setHistoryLoading(false);

      try {
        const [resMsgs, resSess] = await Promise.all([
          getMessages(derivedSessionNo),
          getSession(derivedSessionNo),
        ]);

        const page = resMsgs.data.result as MessagePage;
        const sessionInfo = resSess.data.result as { llmNo?: string; llmName?: string } | undefined;
        const llmName: string = sessionInfo?.llmName ?? selectedModel ?? 'Qwen3-vl:8B';
        const llmNoFromSession = sessionInfo?.llmNo ?? selectedLlmNo;

        setSelectedModel(llmName, llmNoFromSession);
        setLlmNo(llmNoFromSession ?? null);

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

          const nextCursor = page.pagination.nextCursor ?? null;
          setHistoryCursor(nextCursor);
          setHasMoreHistory(Boolean(nextCursor));

          requestAnimationFrame(() => bottomRef.current?.scrollIntoView());
        }
      } catch {
        if (!cancelled) {
          setList([]);
          setHasMoreHistory(false);
        }
      } finally {
        if (!cancelled) setInitialLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [derivedSessionNo, setSelectedModel]);

  const loadOlderMessages = async () => {
    if (!currentSessionNo) return;
    if (historyLoading) return;
    if (!historyCursor) return;
    if (!hasMoreHistory) return;

    const el = scrollRef.current;
    const prevScrollHeight = el?.scrollHeight ?? 0;

    setHistoryLoading(true);
    try {
      const res = await getMessages(currentSessionNo, {
        cursor: historyCursor,
        limit: 20,
      });

      const page = res.data.result as MessagePage;

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

      setList((prev) => [...mapped, ...prev]);

      const nextCursor = page.pagination?.nextCursor ?? null;
      setHistoryCursor(nextCursor);
      setHasMoreHistory(Boolean(nextCursor) && mapped.length > 0);

      requestAnimationFrame(() => {
        if (!el) return;
        const newScrollHeight = el.scrollHeight;
        el.scrollTop = newScrollHeight - prevScrollHeight;
      });
    } catch {
      setHasMoreHistory(false);
    } finally {
      setHistoryLoading(false);
    }
  };

  const isAtBottom = () => {
    const doc = document.documentElement;
    const scrollTop = window.scrollY || doc.scrollTop;
    const clientHeight = window.innerHeight;
    const scrollHeight = doc.scrollHeight;

    return scrollTop + clientHeight >= scrollHeight - 50;
  };

  useEffect(() => {
    if (forceScrollRef.current) {
      forceScrollRef.current = false;
      requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }));
      return;
    }
    if (isAtBottom()) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [list.length]);

  useEffect(() => {
    const handleWindowScroll = () => {
      const doc = document.documentElement;
      const scrollTop = window.scrollY || doc.scrollTop;

      // 위쪽(페이지 최상단 근처) 도달 시 지난 히스토리 로딩
      if (!historyLoading && hasMoreHistory && scrollTop <= 30) {
        void loadOlderMessages();
      }
    };

    window.addEventListener('scroll', handleWindowScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleWindowScroll);
  }, [historyLoading, hasMoreHistory, historyCursor, currentSessionNo]);

  const fillPendingAssistant = (content: string, createdAt?: string, messageNo?: string) => {
    setList((prev: UiMsg[]) =>
      prev.map(
        (m: UiMsg): UiMsg =>
          m.messageNo === '__pending__'
            ? {
                role: 'assistant',
                content: content || '(응답이 없습니다)',
                createdAt: createdAt ?? m.createdAt,
                messageNo: messageNo ?? m.messageNo,
              }
            : m
      )
    );
  };

  const handleSend = async (msg: string) => {
    forceScrollRef.current = true;
    setAwaitingAssistant(true);

    setList((prev) => [
      ...prev,
      { role: 'user', content: msg },
      { role: 'assistant', content: '', messageNo: '__pending__' },
    ]);

    try {
      const llmName: string = selectedModel ?? 'Qwen3-vl:8B';
      const sessionNo: string = await getOrCreateSessionNo(llmName, msg);

      if (mode === 'rag') {
        const effectiveLlmNo = llmNo ?? selectedLlmNo;
        if (!effectiveLlmNo) {
          toast.error('LLM 정보가 없습니다. 세션 정보를 다시 불러와 주세요.');
          throw new Error('LLM 정보가 없습니다.');
        }

        const res = await postRagQuery({
          llmNo: effectiveLlmNo,
          sessionNo,
          query: msg,
        });
        const result = res.data.result as RagQueryProcessResult;

        forceScrollRef.current = true;
        fillPendingAssistant(
          result.content ?? '(응답이 없습니다)',
          result.createdAt,
          result.messageNo
        );
      } else {
        const body: SendMessageRequest = { content: msg, model: llmName };
        const res = await sendMessage(sessionNo, body);
        const result = res.data.result as SendMessageResult;

        const content = result.content ?? '(응답이 없습니다)';
        const createdAt = result?.createdAt ?? undefined;
        const messageNo = result?.messageNo ?? undefined;

        forceScrollRef.current = true;
        fillPendingAssistant(content, createdAt, messageNo);
      }
    } catch (e) {
      console.error(e);
      setList((prev: UiMsg[]) => prev.filter((m: UiMsg) => m.messageNo !== '__pending__'));
    } finally {
      setAwaitingAssistant(false);
    }
  };

  const thinkingSubtitle = useThinkingTicker(awaitingAssistant);

  if (initialLoading) {
    return (
      <section className="flex flex-col min-h-[calc(100vh-82px)]">
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="bg-gray-100 px-4 py-3 rounded-2xl shadow-sm flex items-center gap-2">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.2s]" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.1s]" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="flex min-h-[calc(100vh-82px)] flex-col">
      {list.length > 0 ? (
        <>
          <div
            ref={scrollRef}
            className="relative flex-1 min-h-0 w-full flex justify-center overflow-y-auto no-scrollbar"
          >
            <div className="w-full h-full max-w-[75%] space-y-10 px-12 py-4">
              {historyLoading && (
                <div className="flex justify-center py-3">
                  <div className="bg-gray-100 px-4 py-2 rounded-2xl shadow-sm flex items-center gap-2">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.2s]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.1s]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  </div>
                </div>
              )}

              {list.map((m, i) => (
                <ChatMessageItem
                  key={`${m.messageNo ?? 'pending'}-${i}`}
                  msg={m}
                  index={i}
                  currentSessionNo={currentSessionNo}
                  isEditing={m.role === 'user' && editingIdx === i}
                  editingDraft={editingDraft}
                  onStartReask={startReask}
                  onCancelReask={cancelReask}
                  onSubmitReask={submitReask}
                  isPendingAssistant={awaitingAssistant && m.role === 'assistant' && !m.content}
                  pendingSubtitle={thinkingSubtitle}
                  brand="hebees"
                  enableDocuments={mode === 'rag'}
                />
              ))}

              <div ref={bottomRef} className="h-6" />
            </div>
          </div>

          <div className="sticky bottom-0 w-full flex justify-center">
            <div className="w-full max-w-[75%]">
              <ChatInput
                onSend={handleSend}
                variant="hebees"
                mode={mode}
                onChangeMode={setMode}
                watch={list.length}
              />
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center ">
          <div className="w-full max-w-[75%] flex flex-col items-center gap-4 text-center">
            <ChatEmptyState onSelectPrompt={handleSend} />
            <div className="w-full">
              <div className="bg-white pb-4">
                <ChatInput
                  onSend={handleSend}
                  variant="hebees"
                  mode={mode}
                  onChangeMode={setMode}
                  watch={list.length}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
