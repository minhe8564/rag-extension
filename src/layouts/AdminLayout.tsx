import { useState, useEffect, useCallback } from 'react';
import { Outlet, NavLink, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import {
  Menu,
  Settings,
  Monitor,
  FolderCog,
  MessageSquare,
  Bell,
  LogOut,
  UserCog,
  Users,
  Search,
  Image,
} from 'lucide-react';
import Tooltip from '@/shared/components/controls/Tooltip';
import ChatList from '@/shared/components/chat/list/ChatList';
import ChatSearchModal from '@/shared/components/chat/layout/ChatSearchModal';
import { AlertModal } from '@/layouts/AlertModal';
import HebeesLogo from '@/assets/hebees-logo.png';
import Select from '@/shared/components/controls/Select';
import type { Option } from '@/shared/components/controls/Select';
import { getMyLlmKeys } from '@/shared/api/llm.api';
import type { MyLlmKeyResponse, MyLlmKeyListResponse } from '@/shared/types/llm.types';

import { useAuthStore } from '@/domains/auth/store/auth.store';
import { useChatModelStore } from '@/shared/store/useChatModelStore';
import { useIngestNotifyStream } from '@/shared/hooks/useIngestNotifyStream';
import type { IngestSummaryResponse } from '@/shared/types/ingest.types';
import { useNotificationStore } from '@/shared/store/useNotificationStore';
import { useIngestStreamStore } from '@/shared/store/useIngestStreamStore';
import {
  useNotificationsQuery,
  useMarkReadMutation,
  useDeleteNotificationMutation,
} from '@/shared/hooks/useNotificationQuery';

const labelCls = (isOpen: boolean) =>
  'ml-2 whitespace-nowrap transition-[max-width,opacity,transform] duration-300 ' +
  (isOpen
    ? 'max-w-[8rem] opacity-100 translate-x-0'
    : 'max-w-0 opacity-0 -translate-x-2 pointer-events-none');

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
  (isActive
    ? 'bg-[var(--color-hebees-bg)] text-[var(--color-hebees)]'
    : 'text-gray-700 hover:bg-[var(--color-hebees)] hover:text-white');

const MODEL_DESCRIPTIONS: Record<string, string> = {
  'Qwen3-vl:8B': '가볍고 빠른 멀티모달 모델',
  'GPT-4o': '전반적인 품질·안정성 균형',
  'Gemini 2.5 Flash': '대용량 문서·검색 작업에 최적',
  'Claude Sonnet 4': '복잡한 분석·글쓰기·요약에 강점',
};

export default function UserLayout() {
  const [isOpen, setIsOpen] = useState(true);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const navigate = useNavigate();

  const [completedCount, setCompletedCount] = useState(0);

  const [sp] = useSearchParams();
  const location = useLocation();
  const { pathname } = location;

  const sessionFromPath = pathname.startsWith('/admin/chat/text/')
    ? pathname.replace('/admin/chat/text/', '')
    : undefined;

  const sessionFromQuery = sp.get('session') || undefined;

  const activeSessionNo = sessionFromPath ?? sessionFromQuery;

  const isChatRoute = pathname.startsWith('/admin/chat/text');

  const [modelOptions, setModelOptions] = useState<Option[]>([]);
  const [llmList, setLlmList] = useState<MyLlmKeyResponse[]>([]);
  const { selectedModel, setSelectedModel } = useChatModelStore();
  const [alertModal, setAlertModal] = useState(false);

  const loadLlmKeys = useCallback(async () => {
    try {
      const res = await getMyLlmKeys();
      const result = res.data.result as MyLlmKeyListResponse;
      const list: MyLlmKeyResponse[] = result?.data ?? [];

      const isQwen = (llmName: string | null | undefined): boolean => {
        if (!llmName) return false;
        const name = llmName.toLowerCase();
        return name.includes('qwen');
      };

      const filteredList = list.filter((k) => isQwen(k.llmName) || k.hasKey);

      const options: Option[] = filteredList
        .map((k) => ({
          value: k.llmName ?? '',
          label: k.llmName ?? '',
          desc: k.llmName ? (MODEL_DESCRIPTIONS[k.llmName] ?? '모델 설명 없음') : '모델 정보 없음',
        }))
        .filter((o) => o.value);

      setModelOptions(options);
      setLlmList(filteredList);

      const { selectedModel: currentSelectedModel, setSelectedModel: setModel } =
        useChatModelStore.getState();

      let final = currentSelectedModel;
      const found = filteredList.find((k) => k.llmName === final);

      if (!found) {
        final = filteredList[0]?.llmName;
      }

      if (final) {
        const matched = filteredList.find((k) => k.llmName === final);
        setModel(final, matched?.llmNo);
      } else {
        setModel(undefined, undefined);
      }
    } catch (err) {
      console.error(err);
      setModelOptions([]);
      const { setSelectedModel: setModel } = useChatModelStore.getState();
      setModel(undefined, undefined);
    }
  }, []);

  const accessToken = useAuthStore((s) => s.accessToken);
  const addIngestNotification = useNotificationStore((s) => s.addIngestNotification);

  const enabled = useIngestStreamStore((s) => s.enabled);
  const setEnabled = useIngestStreamStore((s) => s.setEnabled);

  // 알림 쿼리
  const { data } = useNotificationsQuery({ cursor: '', limit: '20' }, alertModal);
  const notifications = data?.data ?? []; // 리스트
  const { mutate: markAsRead } = useMarkReadMutation();
  const { mutate: deleteNoti } = useDeleteNotificationMutation();
  const hasUnreadRealtime = useNotificationStore((s) => s.hasUnreadRealtime);

  const handleBellClick = () => {
    // 완료 뱃지도 초기화
    setCompletedCount(0);
    setAlertModal((prev) => !prev);
  };

  function extractCompleted(data: IngestSummaryResponse): number | null {
    const completed = data.result?.completed;
    return typeof completed === 'number' ? completed : null;
  }

  useIngestNotifyStream({
    accessToken: accessToken ?? '',
    enabled,
    onMessage: (data) => {
      addIngestNotification(data);

      const completed = extractCompleted(data);
      if (completed !== null) {
        setCompletedCount(completed);
      }

      setEnabled(false);
    },
    onError: (e) => {
      console.error('Ingest SSE error: ', e);
      setEnabled(false);
    },
  });

  useEffect(() => {
    if (!isChatRoute) return;
    void loadLlmKeys();
  }, [isChatRoute, loadLlmKeys]);

  return (
    <div className="flex min-h-screen bg-transparent">
      <aside
        className={`sticky top-0 self-start shrink-0 h-dvh flex flex-col bg-white transition-all duration-300 shadow-sm ${
          isOpen ? 'w-64 border-r' : 'w-[64px] border-r'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-5">
          {isOpen ? (
            <div className="text-base font-semibold">
              <img src={HebeesLogo} alt="Hebees" className="w-28 h-9 object-contain" />
            </div>
          ) : (
            <div className="w-full flex justify-center">
              <Tooltip content="사이드바 열기" side="right" shiftX={12} portal={true}>
                <button
                  onClick={() => setIsOpen((prev) => !prev)}
                  className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-dark)]"
                >
                  <Menu size={22} />
                </button>
              </Tooltip>
            </div>
          )}

          {isOpen && (
            <Tooltip content="사이드바 닫기" side="right" shiftX={12} portal={true}>
              <button
                onClick={() => setIsOpen(false)}
                className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-dark)]"
              >
                <Menu size={22} />
              </button>
            </Tooltip>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-2 mt-1 shrink-0">
          <NavLink to="/admin/dashboard" className={linkCls}>
            {!isOpen ? (
              <Tooltip content="대시보드" side="right" shiftX={12}>
                <span>
                  <Monitor size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <Monitor size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">대시보드</span>
            </div>
          </NavLink>

          <NavLink to="/admin/rag/settings" className={linkCls}>
            {!isOpen ? (
              <Tooltip content="RAG 모델 설정" side="right" shiftX={12}>
                <span>
                  <Settings size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <Settings size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">RAG 모델 설정</span>
            </div>
          </NavLink>

          <NavLink to="/admin/chat/text" className={linkCls}>
            {!isOpen ? (
              <Tooltip content="RAG 채팅" side="right" shiftX={12}>
                <span>
                  <MessageSquare size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <MessageSquare size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">RAG 채팅</span>
            </div>
          </NavLink>

          <NavLink to="/admin/chat/image" className={linkCls}>
            {!isOpen ? (
              <Tooltip content="이미지 생성" side="right" shiftX={12}>
                <span>
                  <Image size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <Image size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">이미지 생성</span>
            </div>
          </NavLink>

          <NavLink to="/admin/documents" className={linkCls}>
            {!isOpen ? (
              <Tooltip content="문서 관리" side="right" shiftX={12}>
                <span>
                  <FolderCog size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <FolderCog size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">문서 관리</span>
            </div>
          </NavLink>

          <button
            type="button"
            className={
              'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
              'text-gray-700 hover:bg-[var(--color-hebees)] hover:text-white'
            }
            onClick={() => setOpen(true)}
          >
            {!isOpen ? (
              <Tooltip content="채팅 검색" side="right" shiftX={12}>
                <span>
                  <Search size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <Search size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">채팅 검색</span>
            </div>
          </button>
        </nav>

        {isOpen && (
          <div className="mt-6 mb-10 px-2 flex-1 min-h-0 overflow-y-auto overflow-x-visible overscroll-contain no-scrollbar">
            <ChatList
              activeSessionNo={activeSessionNo}
              onSelect={(s) => navigate(`/admin/chat/text/${s.sessionNo}`)}
              pageSize={20}
              brand="hebees"
            />
          </div>
        )}

        <div className="mt-auto px-2 pb-4 shrink-0">
          <NavLink
            to="/admin/users"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-hebees-bg)] hover:text-[var(--color-hebees)]"
          >
            {!isOpen ? (
              <Tooltip content="사용자 관리" side="right" shiftX={12}>
                <span>
                  <Users size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <Users size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">사용자 관리</span>
            </div>
          </NavLink>

          <NavLink
            to="/admin/profile"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-hebees-bg)] hover:text-[var(--color-hebees)]"
          >
            {!isOpen ? (
              <Tooltip content="내 정보 관리" side="right" shiftX={12}>
                <span>
                  <UserCog size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <UserCog size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">내 정보 관리</span>
            </div>
          </NavLink>

          <NavLink
            to="/logout"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-hebees-bg)] hover:text-[var(--color-hebees)]"
          >
            {!isOpen ? (
              <Tooltip content="로그아웃" side="right" shiftX={12}>
                <span>
                  <LogOut size={18} className="flex-shrink-0" />
                </span>
              </Tooltip>
            ) : (
              <LogOut size={18} className="flex-shrink-0" />
            )}
            <div className={labelCls(isOpen)}>
              <span className="inline-block">로그아웃</span>
            </div>
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <div
          className={`sticky z-[9999] top-0 flex px-8 py-5 ${
            isChatRoute ? 'justify-between' : 'justify-end'
          }`}
        >
          {isChatRoute && modelOptions.length > 0 && (
            <Select
              options={modelOptions}
              value={selectedModel}
              onChange={(v) => {
                const matched = llmList.find((k) => k.llmName === v);
                setSelectedModel(v, matched?.llmNo);
              }}
              className="w-[190px]"
            />
          )}

          <Tooltip
            content={completedCount > 0 ? `Ingest 완료: ${completedCount}건` : '알림'}
            side="bottom"
            shiftX={completedCount > 0 ? -20 : 0}
          >
            <button
              type="button"
              onClick={handleBellClick}
              className="flex items-center justify-center"
            >
              <div className="relative">
                <Bell
                  size={22}
                  className="text-gray-600 hover:text-gray-800 cursor-pointer transition-colors shake-hover"
                />
                {(completedCount > 0 || hasUnreadRealtime) && (
                  <span
                    className="
                      absolute -top-[4px] -right-[6px]
                      min-w-[16px] h-[16px]
                      rounded-full bg-red-500 text-white text-[10px]
                      flex items-center justify-center
                      leading-none px-[4px]
                    "
                  >
                    {completedCount || 1}
                  </span>
                )}
                <AlertModal
                  isOpen={alertModal}
                  onClose={() => setAlertModal(false)}
                  notifications={notifications} // 알림 데이터 배열
                  onRead={(no) => markAsRead(no)} // 개별 읽음 처리
                  onDelete={(no) => deleteNoti(no)} // 개별 삭제 처리
                />
              </div>
            </button>
          </Tooltip>
        </div>

        <div className="flex w-full flex-col gap-3 px-8">
          <Outlet key={pathname + location.search} />
        </div>
      </main>

      <ChatSearchModal
        open={open}
        value={q}
        onValueChange={setQ}
        onClose={() => setOpen(false)}
        onSelect={(s) => navigate(`/admin/chat/text?session=${s.sessionNo}`)}
      />
    </div>
  );
}
