import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { Menu, MessageSquare, Image, FolderCog, LogOut, Bell, UserCog, Search } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import ChatList from '@/shared/components/chat/list/ChatList';
import ChatSearchModal from '@/shared/components/chat/ChatSearchModal';
import RetinaLogo from '@/assets/retina-logo.png';
import Select from '@/shared/components/Select';
import type { Option } from '@/shared/components/Select';
import { getMyLlmKeys } from '@/shared/api/llm.api';
import type { MyLlmKeyResponse, MyLlmKeyListResponse } from '@/shared/types/llm.types';

const labelCls = (isOpen: boolean) =>
  'ml-2 whitespace-nowrap transition-[max-width,opacity,transform] duration-300 ' +
  (isOpen
    ? 'max-w-[8rem] opacity-100 translate-x-0'
    : 'max-w-0 opacity-0 -translate-x-2 pointer-events-none');

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
  (isActive
    ? 'bg-[var(--color-retina-bg)] text-[var(--color-retina)]'
    : 'text-gray-700 hover:bg-[var(--color-retina)] hover:text-white');

export default function UserLayout() {
  const [isOpen, setIsOpen] = useState(true);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [sp] = useSearchParams();
  const activeSessionNo = sp.get('session') || undefined;
  const navigate = useNavigate();

  const { pathname } = useLocation();
  const isChatRoute = pathname.startsWith('/user/chat/text');

  const [modelOptions, setModelOptions] = useState<Option[]>([]);
  const [modelValue, setModelValue] = useState<string | undefined>(undefined);

  const MODEL_DESCRIPTIONS: Record<string, string> = {
    'Qwen3-vl:8B': '가볍고 빠른 멀티모달 모델',
    'GPT-4o': '전반적인 품질·안정성 균형',
    'Gemini 2.5 Flash': '대용량 문서·검색 작업에 최적',
    'Claude Sonnet 4': '복잡한 분석·글쓰기·요약에 강점',
  };

  useEffect(() => {
    let active = true;

    (async () => {
      try {
        const res = await getMyLlmKeys();
        const result = res.data.result as MyLlmKeyListResponse;
        const list: MyLlmKeyResponse[] = result?.data ?? [];

        const options: Option[] = list.map((k) => ({
          value: k.llmName,
          label: k.llmName,
          desc: MODEL_DESCRIPTIONS[k.llmName] ?? '모델 설명 없음',
        }));

        if (!active) return;

        setModelOptions(options);
        setModelValue((prev) => prev ?? options[0]?.value);
      } catch {
        if (!active) return;
        setModelOptions([]);
        setModelValue(undefined);
      }
    })();

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
              <img src={RetinaLogo} alt="Retina" className="w-28 h-9 object-contain" />
            </div>
          ) : (
            <div className="w-full flex justify-center">
              <Tooltip content="사이드바 열기" side="bottom" shiftX={15}>
                <button
                  onClick={() => setIsOpen((prev) => !prev)}
                  className="text-[var(--color-retina)] hover:text-[var(--color-retina-dark)]"
                >
                  <Menu size={22} />
                </button>
              </Tooltip>
            </div>
          )}

          {isOpen && (
            <Tooltip content="사이드바 닫기" side="bottom" shiftX={15}>
              <button
                onClick={() => setIsOpen(false)}
                className="text-[var(--color-retina)] hover:text-[var(--color-retina-dark)]"
              >
                <Menu size={22} />
              </button>
            </Tooltip>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-2 mt-1 overflow-hidden">
          <NavLink to="/user/chat/text" className={linkCls}>
            <MessageSquare size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">RAG 채팅</span>
            </div>
          </NavLink>

          <NavLink to="/user/chat/image" className={linkCls}>
            <Image size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">이미지 생성</span>
            </div>
          </NavLink>

          <NavLink to="/user/documents" className={linkCls}>
            <FolderCog size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">내 문서 관리</span>
            </div>
          </NavLink>

          <button
            type="button"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-retina)] hover:text-white"
            onClick={() => setOpen(true)}
          >
            <Search size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">채팅 검색</span>
            </div>
          </button>
        </nav>

        {isOpen && (
          <div className="mt-6 mb-10 px-2 flex-1 min-h-0 overflow-y-auto overflow-x-visible overscroll-contain no-scrollbar">
            <ChatList
              activeSessionNo={activeSessionNo}
              onSelect={(s) => navigate(`/user/chat/text/${s.sessionNo}`)}
              pageSize={20}
              brand="retina"
            />
          </div>
        )}

        <div className="mt-auto px-2 pb-4 shrink-0">
          <NavLink
            to="/user/profile"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-retina-bg)] hover:text-[var(--color-retina)]"
          >
            <UserCog size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">내 정보 관리</span>
            </div>
          </NavLink>
          <NavLink
            to="/logout"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-retina-bg)] hover:text-[var(--color-retina)]"
          >
            <LogOut size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">로그아웃</span>
            </div>
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <div
          className={`sticky z-50 top-0 flex px-8 py-5 ${
            isChatRoute ? 'justify-between' : 'justify-end'
          }`}
        >
          {isChatRoute && modelOptions.length > 0 && (
            <Select
              options={modelOptions}
              value={modelValue}
              onChange={setModelValue}
              className="w-[220px]"
              placeholder="모델 선택"
            />
          )}

          <Bell
            size={22}
            className="text-gray-600 hover:text-gray-800 cursor-pointer transition-colors shake-hover"
          />
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
        onSelect={(s) => navigate(`/user/chat/text?session=${s.sessionNo}`)}
      />
    </div>
  );
}
