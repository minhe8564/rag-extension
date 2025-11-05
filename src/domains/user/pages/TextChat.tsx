import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import ChatInput from '@/shared/components/chat/ChatInput';
import Tooltip from '@/shared/components/Tooltip';
import { toast } from 'react-toastify';
import { formatIsoDatetime } from '@/shared/util/iso';
import { Wand2 } from 'lucide-react';
import InlineReaskInput from '@/shared/components/chat/InlineReaskInput';
import ReferencedDocsPanel from '@/shared/components/chat/ReferencedDocs';

import type {
  ChatRole,
  MessageItem,
  MessagePage,
  SendMessageRequest,
  SendMessageResult,
  CreateSessionResult,
  ReferencedDocument,
} from '@/shared/types/chat.types';

import { getMessages, sendMessage, createSession } from '@/shared/api/chat.api';

type UiRole = 'user' | 'assistant' | 'system' | 'tool';
type UiMsg = {
  role: UiRole;
  content: string;
  createdAt?: string;
  messageNo?: string;
  referencedDocuments?: ReferencedDocument[];
};

const mapRole = (r: ChatRole): UiRole => (r === 'human' ? 'user' : r === 'ai' ? 'assistant' : r);

const deriveSessionNo = (
  pathname: string,
  searchParams: URLSearchParams,
  paramsSessionNo?: string
) => {
  if (paramsSessionNo) return paramsSessionNo;
  const byQuery = searchParams.get('session');
  if (byQuery) return byQuery;
  const legacy = pathname.match(/\/chat\/text:session=([^/]+)/);
  return legacy?.[1] ?? null;
};

export default function TextChat() {
  const { sessionNo: paramsSessionNo } = useParams<{ sessionNo: string }>();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  const derivedSessionNo = useMemo(
    () => deriveSessionNo(location.pathname, searchParams, paramsSessionNo),
    [location.pathname, searchParams, paramsSessionNo]
  );

  const [currentSessionNo, setCurrentSessionNo] = useState<string | null>(derivedSessionNo);
  const [list, setList] = useState<UiMsg[]>([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // 사용자 메시지 인라인 편집(질문 재생성)
  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editingDraft, setEditingDraft] = useState<string>('');

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

  useEffect(() => {
    if (!derivedSessionNo) return;
    setCurrentSessionNo(derivedSessionNo);

    (async () => {
      try {
        setLoading(true);
        const res = await getMessages(derivedSessionNo);
        const page: MessagePage = res.data.result;

        const mapped: UiMsg[] =
          page.data?.map((m: MessageItem) => ({
            role: mapRole(m.role),
            content: m.content,
            createdAt: m.createdAt,
            messageNo: m.messageNo,
            referencedDocuments: m.referencedDocuments,
          })) ?? [];

        setList(mapped);

        // 쿼리/레거시 진입이면 주소 정규화
        if (location.pathname.includes('text:session=') || location.search.includes('session=')) {
          window.history.replaceState(history.state, '', `/user/chat/text/${derivedSessionNo}`);
        }

        requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: 'auto' }));
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, [derivedSessionNo]);

  // 새 메시지 추가 시 맨 아래로
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [list.length]);

  const ensureSession = async () => {
    if (currentSessionNo) return currentSessionNo;
    const created = await createSession({});
    const data: CreateSessionResult = created.data.result;
    setCurrentSessionNo(data.sessionNo);
    window.history.replaceState(history.state, '', `/user/chat/text/${data.sessionNo}`);
    return data.sessionNo;
  };

  const handleSend = async (msg: string) => {
    setList((prev) => [...prev, { role: 'user', content: msg }]);
    try {
      const sessionNo = await ensureSession();
      const body: SendMessageRequest = { content: msg };
      const res = await sendMessage(sessionNo, body);
      const result: SendMessageResult = res.data.result;

      const assistant: UiMsg = {
        role: 'assistant',
        content: result.content ?? '(응답이 없습니다)',
        createdAt: result.timestamp,
        // result.messageNo가 있다면 여기에 넣어주세요.
        // messageNo: result.messageNo,
      };
      setList((prev) => [...prev, assistant]);
    } catch (e) {
      console.error(e);
      toast.error('메시지 전송에 실패했어요.');
    }
  };

  const hasMessages = list.length > 0;

  return (
    <section className="h-[calc(100vh-62px)] flex flex-col z-0">
      {hasMessages ? (
        <>
          <div className="flex-1 min-h-0 w-full flex justify-center overflow-y-scroll no-scrollbar">
            <div className="w-full max-w-[75%] space-y-6 px-12 py-4">
              {list.map((m, i) => {
                const isUser = m.role === 'user';
                const isEditingThis = isUser && editingIdx === i;

                return (
                  <div
                    key={m.messageNo ?? i}
                    className={
                      'w-fit max-w-[75%] rounded-md border p-3 relative group break-words ' +
                      (isUser ? 'ml-auto bg-[var(--color-retina-bg)] text-black' : 'bg-white')
                    }
                  >
                    {/* 본문: 사용자 메시지 에디팅 시 인라인 입력 박스로 대체 */}
                    {isEditingThis ? (
                      <InlineReaskInput
                        initialValue={editingDraft || m.content}
                        onCancel={cancelReask}
                        onSubmit={submitReask}
                        placeholder="질문을 수정하세요… (Enter 전송, Shift+Enter 줄바꿈)"
                      />
                    ) : (
                      <div className="whitespace-pre-wrap">{m.content}</div>
                    )}

                    {/* assistant 타임스탬프 */}
                    {!isUser && m.createdAt && (
                      <div className="text-[10px] text-gray-400 mt-1">
                        {formatIsoDatetime(m.createdAt)}
                      </div>
                    )}

                    {/* 액션바: 사용자 = 질문 재생성만, 어시스턴트는 생략 */}
                    <div
                      className={`
                        absolute flex gap-2 items-center
                        ${isUser ? 'right-2' : 'left-2'}
                        bottom-[-30px] opacity-0 group-hover:opacity-100
                        transition-opacity duration-200
                      `}
                    >
                      {isUser && !isEditingThis && (
                        <Tooltip content="질문 재생성 (수정 후 전송)" side="bottom">
                          <button
                            onClick={() => startReask(i, m.content)}
                            className="p-1 rounded hover:bg-gray-100"
                          >
                            <Wand2 size={14} className="text-gray-500" />
                          </button>
                        </Tooltip>
                      )}
                    </div>

                    {/* 어시스턴트 메시지의 참조 문서 패널 */}
                    {!isUser && m.messageNo && currentSessionNo ? (
                      <ReferencedDocsPanel
                        sessionNo={currentSessionNo}
                        messageNo={m.messageNo}
                        collapsedByDefault={false}
                      />
                    ) : null}
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          </div>

          <div className="sticky bottom-0 shrink-0 w-full flex justify-center pb-5 bg-white">
            <div className="w-full max-w-[75%]">
              <ChatInput onSend={handleSend} variant="retina" />
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 min-h-[calc(100vh-62px)] flex items-center justify-center px-4">
          <div className="w-full max-w-[75%] flex flex-col items-center gap-6 text-center">
            <ChatInput onSend={handleSend} variant="retina" />
          </div>
        </div>
      )}
    </section>
  );
}
