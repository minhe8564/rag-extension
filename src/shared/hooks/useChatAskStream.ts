import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchEventSource, type EventSourceMessage } from '@microsoft/fetch-event-source';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import type { SendMessageRequest, ReferencedDocument } from '@/shared/types/chat.types';
import { parseData } from '@/shared/utils/sse';

const springBase = import.meta.env.VITE_SPRING_BASE_URL;
const ragBase = import.meta.env.VITE_GATEWAY_BASE_URL;

type ChatInitEvent = {
  messageNo: string;
  role: 'ai';
  createdAt: string;
  references?: ReferencedDocument[];
};

type ChatUpdateEvent = {
  content: string;
};

type UseChatAskStreamOptions = {
  sessionNo?: string;
  urlType?: 'session' | 'plain' | 'rag';
  withCredentials?: boolean;
};

// 1. 스트리밍 기반으로 LLM/RAG 챗 요청을 보내고 토큰을 실시간으로 받아오는 훅
export function useChatAskStream(opts: UseChatAskStreamOptions = {}) {
  const token = useAuthStore.getState().accessToken;

  // 2. 스트리밍 상태 관리
  const [isStreaming, setIsStreaming] = useState(false);
  const [answer, setAnswer] = useState('');
  const [meta, setMeta] = useState<ChatInitEvent | null>(null);
  const [errorText, setErrorText] = useState<string | null>(null);

  // 3. 중복 스트림 방지 및 stale 이벤트 무시 처리
  const controllerRef = useRef<AbortController | null>(null);
  const streamIdRef = useRef(0);

  // 4. urlType(session/plain/rag)에 따라 SSE 요청 URL 계산
  const resolveUrl = useCallback(
    (body: SendMessageRequest) => {
      const urlType = opts.urlType ?? (opts.sessionNo ? 'session' : 'plain');

      if (urlType === 'session') {
        const sessionNo = body.sessionNo ?? opts.sessionNo;
        if (!sessionNo) throw new Error('sessionUrl 사용 시 sessionNo는 필수입니다.');
        return `${springBase}/api/v1/chat/sessions/${sessionNo}/ask/stream`;
      }

      if (urlType === 'rag') {
        return `${ragBase}/rag/query/process/stream`;
      }

      return `${springBase}/api/v1/chat/ask/stream`;
    },
    [opts.sessionNo, opts.urlType]
  );

  // 5. 스트리밍 시작 (SSE 연결)
  const startStream = useCallback(
    (body: SendMessageRequest) => {
      if (!token) {
        setErrorText('로그인이 필요합니다.');
        return;
      }

      // 기존 연결 중단
      if (controllerRef.current) {
        controllerRef.current.abort();
        controllerRef.current = null;
      }

      // 새 스트림 ID
      streamIdRef.current += 1;
      const currentStreamId = streamIdRef.current;

      // 초기화
      setIsStreaming(true);
      setAnswer('');
      setMeta(null);
      setErrorText(null);

      let url: string;
      try {
        url = resolveUrl(body);
      } catch (e) {
        if (currentStreamId !== streamIdRef.current) return;
        setIsStreaming(false);
        setErrorText(e instanceof Error ? e.message : '요청 URL 생성 실패');
        return;
      }

      const payload: Record<string, unknown> = {};
      if (body.query != null) payload.query = body.query;
      if (body.content != null) payload.content = body.content;
      if (body.llmNo != null) payload.llmNo = body.llmNo;
      if (body.model != null) payload.model = body.model;
      if (body.sessionNo != null) payload.sessionNo = body.sessionNo;

      const headers: Record<string, string> = {
        Authorization: `Bearer ${token}`,
        Accept: 'text/event-stream',
        'Content-Type': 'application/json',
      };

      const controller = new AbortController();
      controllerRef.current = controller;

      const credentials: RequestCredentials = opts.withCredentials ? 'include' : 'same-origin';

      // SSE 연결
      void fetchEventSource(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: controller.signal,
        credentials,

        // 6. 연결 오픈
        async onopen(response) {
          if (currentStreamId !== streamIdRef.current) return;

          if (!response.ok) {
            setErrorText(
              response.status === 401
                ? '로그인이 만료되었어요. 다시 로그인해 주세요.'
                : `응답 스트림 연결 실패 (status: ${response.status})`
            );
            setIsStreaming(false);
            controller.abort();
          }
        },

        // 7. 서버가 보낸 토큰을 받을 때마다 실행
        onmessage(msg: EventSourceMessage) {
          if (currentStreamId !== streamIdRef.current) return;

          const event = msg.event || 'update';

          if (event === 'init') {
            const data = parseData<ChatInitEvent>(msg.data);
            if (data) {
              setMeta(data);
              setErrorText(null);
            }
            return;
          }

          if (event === 'update' || event === 'message') {
            const data = parseData<ChatUpdateEvent>(msg.data);
            if (data?.content) {
              setAnswer((prev) => prev + data.content);
            }
          }
        },

        // 8. 오류 발생 시 처리
        onerror() {
          if (currentStreamId !== streamIdRef.current) return;

          if (!controller.signal.aborted) {
            setIsStreaming(false);
            setErrorText('응답 스트림 처리 중 오류가 발생했어요.');
            controller.abort();
          }
        },
      }).finally(() => {
        // 9. 스트림 종료 처리
        if (currentStreamId !== streamIdRef.current) return;

        if (!controller.signal.aborted) setIsStreaming(false);
        if (controllerRef.current === controller) controllerRef.current = null;
      });
    },
    [opts.withCredentials, resolveUrl, token]
  );

  // 10. 스트림 강제 중단
  const stopStream = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }

    streamIdRef.current += 1;

    setIsStreaming(false);
    setAnswer('');
    setMeta(null);
  }, []);

  // 11. 언마운트 시 스트림 정리
  useEffect(() => {
    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort();
        controllerRef.current = null;
      }
      streamIdRef.current += 1;
    };
  }, []);

  return {
    isStreaming,
    answer,
    meta,
    errorText,
    startStream,
    stopStream,
  };
}
