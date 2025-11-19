import { useEffect, useRef, useState } from 'react';
import { useLocation, useParams, useSearchParams } from 'react-router-dom';
import { getSession, getMessages /* , sendMessage */ } from '@/shared/api/chat.api';
import type { UiMsg, UiRole } from '@/shared/components/chat/message/ChatMessageItem';
import type {
  ChatRole,
  MessageItem,
  MessagePage,
  SendMessageRequest,
  // SendMessageResult,
} from '@/shared/types/chat.types';
import {
  useDerivedSessionNo,
  useEnsureSession,
  useThinkingTicker,
} from '@/domains/user/hooks/useChatHelpers';
import { useChatModelStore } from '@/shared/store/useChatModelStore';
// import type { RagQueryProcessResult } from '@/shared/types/chat.rag.types';
// import { postRagQuery } from '@/shared/api/chat.rag.api';
import { toast } from 'react-toastify';
import { useChatAskStream } from '@/shared/hooks/useChatAskStream';

// 1. ChatRole을 UI용 UiRole로 매핑하는 유틸 함수
const mapRole = (r: ChatRole): UiRole => (r === 'human' ? 'user' : r === 'ai' ? 'assistant' : r);

type ChatMode = 'llm' | 'rag';

// 2. 메인 채팅 훅: 세션 관리, 메시지 리스트, LLM/RAG 스트림 제어
export function useChatLogic() {
  const { sessionNo: paramsSessionNo } = useParams<{ sessionNo: string }>();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const derivedSessionNo = useDerivedSessionNo(location, searchParams, paramsSessionNo, 'user');

  const [currentSessionNo, setCurrentSessionNo] = useState<string | null>(derivedSessionNo);
  const [list, setList] = useState<UiMsg[]>([]);
  const [awaitingAssistant, setAwaitingAssistant] = useState(false);
  const [initialLoading, setInitialLoading] = useState<boolean>(Boolean(derivedSessionNo));

  const ensureSession = useEnsureSession(setCurrentSessionNo, 'user');
  const sessionPromiseRef = useRef<Promise<string> | null>(null);

  const { selectedModel, selectedLlmNo, setSelectedModel } = useChatModelStore();

  const [mode, setMode] = useState<ChatMode>('llm');

  // LLM 스트림
  const {
    isStreaming: isLlmStreaming,
    answer: llmAnswer,
    meta: llmMeta,
    startStream: startLlmStream,
    stopStream: stopLlmStream,
  } = useChatAskStream({ urlType: 'session' });

  // RAG 스트림
  const {
    isStreaming: isRagStreaming,
    answer: ragAnswer,
    meta: ragMeta,
    startStream: startRagStream,
    stopStream: stopRagStream,
  } = useChatAskStream({ urlType: 'rag' });

  const isStreaming = isLlmStreaming || isRagStreaming;
  const answer = mode === 'rag' ? ragAnswer : llmAnswer;
  const meta = mode === 'rag' ? ragMeta : llmMeta;

  // 2-1. SSE answer 값을 pending assistant 메시지에 실시간으로 반영
  // SSE answer → pending assistant 메시지에 반영
  useEffect(() => {
    if (!isStreaming) return;
    if (!answer) return;

    setList((prev: UiMsg[]) =>
      prev.map(
        (m: UiMsg): UiMsg =>
          m.messageNo === '__pending__' && m.role === 'assistant' ? { ...m, content: answer } : m
      )
    );
  }, [answer, isStreaming, setList]);

  // 스트림 종료 시 meta 정보로 최종 메시지 확정
  // useEffect(() => {
  //   if (isStreaming) return;
  //   if (!meta) return;
  //   if (!answer) return;
  //
  //   setList((prev: UiMsg[]) =>
  //     prev.map(
  //       (m: UiMsg): UiMsg =>
  //         m.messageNo === '__pending__' && m.role === 'assistant'
  //           ? {
  //               ...m,
  //               content: answer,
  //               createdAt: meta.createdAt ?? m.createdAt,
  //               messageNo: meta.messageNo ?? m.messageNo,
  //             }
  //           : m
  //     )
  //   );
  // }, [isStreaming, meta, answer, setList]);

  // 2-2. 스트림 종료 시 meta 정보(시간/번호/레퍼런스)로 pending 메시지를 최종 확정
  useEffect(() => {
    if (isStreaming) return;
    if (!meta) return;
    if (!answer) return;

    setList((prev: UiMsg[]) => {
      const updated = prev.map(
        (m: UiMsg): UiMsg =>
          m.messageNo === '__pending__' && m.role === 'assistant'
            ? {
                ...m,
                content: answer,
                createdAt: meta.createdAt ?? m.createdAt,
                messageNo: meta.messageNo ?? m.messageNo,
                references: meta.references ?? m.references,
              }
            : m
      );

      return updated;
    });
  }, [isStreaming, meta, answer, setList]);

  // 2-3. LLM/RAG 스트리밍 상태에 따라 awaitingAssistant 동기화
  // LLM 모드일 때는 SSE 상태에 맞춰 awaitingAssistant 동기화
  useEffect(() => {
    setAwaitingAssistant(isStreaming);
  }, [isStreaming]);

  const [editingIdx, setEditingIdx] = useState<number | null>(null);
  const [editingDraft, setEditingDraft] = useState<string>('');

  const requestIdRef = useRef<number | null>(null);

  // 2-4. 세션 번호가 있을 경우 메시지/세션 정보 초기 로딩
  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (!derivedSessionNo) {
        if (!selectedModel) setSelectedModel('GPT-4o', selectedLlmNo);
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
        const llmNoFromSession = sessionInfo?.llmNo ?? selectedLlmNo;

        setSelectedModel(llmName, llmNoFromSession);

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

        if (!cancelled) {
          setList(mapped);
        }
      } catch {
        if (!cancelled) {
          setList([]);
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

  // 2-5. 세션 번호가 없을 경우 새 세션을 생성하거나 기존 세션 번호를 반환
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

  // 2-6. 현재 진행 중인 LLM/RAG 응답 스트림 중단 및 pending 메시지 제거
  const stopCurrentResponse = () => {
    if (!awaitingAssistant && !isStreaming) return;

    requestIdRef.current = null;
    setAwaitingAssistant(false);

    // LLM / RAG 스트림 모두 중단 (실제로 돌고 있는 쪽만 내부에서 abort 됨)
    stopLlmStream();
    stopRagStream();

    setList((prev: UiMsg[]) => prev.filter((m: UiMsg) => m.messageNo !== '__pending__'));
  };

  // 2-7. 사용자 메시지 전송 및 LLM/RAG 스트리밍 시작
  const handleSend = async (msg: string) => {
    if (awaitingAssistant) return;

    const myRequestId = (requestIdRef.current ?? 0) + 1;
    requestIdRef.current = myRequestId;

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
        const effectiveLlmNo = selectedLlmNo;
        if (!effectiveLlmNo) {
          toast.error('LLM 정보가 없습니다. 세션 정보를 다시 불러와 주세요.');
          throw new Error('LLM 정보가 없습니다.');
        }

        // RAG 스트림용 payload
        const body: SendMessageRequest = {
          // 백엔드 RAG SSE에서 기대하는 필드에 맞게 사용
          query: msg,
          llmNo: effectiveLlmNo,
          sessionNo,
        } as SendMessageRequest;

        // RAG 스트리밍 시작
        startRagStream(body);
      } else {
        // const body: SendMessageRequest = { content: msg, model: llmName };
        // const res = await sendMessage(sessionNo, body);
        // const result = res.data.result as SendMessageResult;
        //
        // if (requestIdRef.current !== myRequestId) return;
        //
        // const content = result.content ?? '(응답이 없습니다)';
        // const createdAt = result?.createdAt ?? undefined;
        // const messageNo = result?.messageNo ?? undefined;
        //
        // fillPendingAssistant(content, createdAt, messageNo);
        // LLM 모드: SSE 스트림으로 전환
        const body: SendMessageRequest = { content: msg, model: llmName, sessionNo };
        startLlmStream(body);
        // 나머지 응답 채우기는 위에서 만든 useEffect(answer/meta)에서 처리
      }
    } catch (e) {
      console.error(e);
      if (requestIdRef.current === myRequestId) {
        setList((prev: UiMsg[]) => prev.filter((m: UiMsg) => m.messageNo !== '__pending__'));
      }
    } finally {
      if (requestIdRef.current === myRequestId) {
        setAwaitingAssistant(false);
        requestIdRef.current = null;
      }
    }
  };

  // 2-8. 특정 인덱스의 사용자 메시지를 수정해서 다시 보내기 위한 편집 시작
  const startReask = (idx: number, content: string) => {
    setEditingIdx(idx);
    setEditingDraft(content);
  };

  // 2-9. 재질문 편집 취소
  const cancelReask = () => {
    setEditingIdx(null);
    setEditingDraft('');
  };

  // 2-10. 재질문 내용으로 handleSend 호출 후 상태 초기화
  const submitReask = async (value: string) => {
    await handleSend(value);
    setEditingIdx(null);
    setEditingDraft('');
    toast.success('수정된 질문으로 다시 보냈습니다.');
  };

  // 2-11. 응답 대기 중일 때 "생각 중" 서브 타이틀 텍스트 생성
  const thinkingSubtitle = useThinkingTicker(awaitingAssistant);

  return {
    // 상태
    list,
    mode,
    setMode,
    initialLoading,
    awaitingAssistant,
    thinkingSubtitle,
    editingIdx,
    editingDraft,
    currentSessionNo,

    // 메시지 액션
    handleSend,
    startReask,
    cancelReask,
    submitReask,

    // 리스트 setter (스크롤 훅에서 과거 메시지 붙일 때 사용)
    setList,

    stopCurrentResponse,
  };
}
