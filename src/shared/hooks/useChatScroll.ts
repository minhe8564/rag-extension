import { useEffect, useRef, useState } from 'react';
import { getMessages } from '@/shared/api/chat.api';
import type { UiMsg, UiRole } from '@/shared/components/chat/message/ChatMessageItem';
import type { ChatRole, MessageItem, MessagePage } from '@/shared/types/chat.types';

const mapRole = (r: ChatRole): UiRole => (r === 'human' ? 'user' : r === 'ai' ? 'assistant' : r);

interface UseChatScrollParams {
  currentSessionNo: string | null;
  list: UiMsg[];
  setList: React.Dispatch<React.SetStateAction<UiMsg[]>>;
}

export function useChatScroll({ currentSessionNo, list, setList }: UseChatScrollParams) {
  const [historyCursor, setHistoryCursor] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [hasMoreHistory, setHasMoreHistory] = useState(true);

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const forceScrollRef = useRef(false);
  const skipAutoScrollRef = useRef(false);

  // 초기 리스트가 로딩된 뒤 첫 페이지의 nextCursor 세팅용
  useEffect(() => {
    setHistoryCursor(null);
    setHasMoreHistory(true);
    setHistoryLoading(false);
    skipAutoScrollRef.current = false;
    forceScrollRef.current = true;
  }, [currentSessionNo]);

  const loadOlderMessages = async () => {
    if (!currentSessionNo) return;
    if (historyLoading) return;
    if (!hasMoreHistory && historyCursor === null) return;

    const el = scrollRef.current;
    const prevScrollHeight = el?.scrollHeight ?? 0;

    setHistoryLoading(true);
    try {
      const res = await getMessages(currentSessionNo, {
        cursor: historyCursor ?? undefined,
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
            references: m.references,
          })
        ) ?? [];

      skipAutoScrollRef.current = true;
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

  useEffect(() => {
    if (!bottomRef.current) return;

    if (forceScrollRef.current) {
      forceScrollRef.current = false;
      requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }));
      return;
    }

    if (skipAutoScrollRef.current) {
      skipAutoScrollRef.current = false;
      return;
    }

    requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }));
  }, [list.length]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const handleScroll = () => {
      if (!historyLoading && hasMoreHistory && el.scrollTop <= 30) {
        void loadOlderMessages();
      }
    };

    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [historyLoading, hasMoreHistory, historyCursor, currentSessionNo]);

  const scrollToBottomNow = () => {
    forceScrollRef.current = true;
  };

  return {
    scrollRef,
    bottomRef,
    historyLoading,
    loadOlderMessages,
    scrollToBottomNow,
  };
}
