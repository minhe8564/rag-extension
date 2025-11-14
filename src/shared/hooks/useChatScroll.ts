import { useEffect, useRef, useState } from 'react';
import { getMessages } from '@/shared/api/chat.api';
import type { UiMsg, UiRole } from '@/shared/components/chat/ChatMessageItem';
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

  // 초기 리스트가 로딩된 뒤 첫 페이지의 nextCursor 세팅용
  useEffect(() => {
    if (!currentSessionNo) return;
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
    if (!bottomRef.current) return;

    if (forceScrollRef.current) {
      forceScrollRef.current = false;
      requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }));
      return;
    }

    if (isAtBottom()) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [list.length]);

  useEffect(() => {
    const handleWindowScroll = () => {
      const doc = document.documentElement;
      const scrollTop = window.scrollY || doc.scrollTop;
      if (!historyLoading && hasMoreHistory && scrollTop <= 30) {
        void loadOlderMessages();
      }
    };

    window.addEventListener('scroll', handleWindowScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleWindowScroll);
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
