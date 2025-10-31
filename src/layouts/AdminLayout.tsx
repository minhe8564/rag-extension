import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import {
  Menu,
  Settings,
  Monitor,
  FolderCog,
  MessageCirclePlus,
  Bot,
  Bell,
  LogOut,
} from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import HebeesLogo from '@/assets/hebees-logo.png';

const labelCls = (isOpen: boolean) =>
  'ml-2 overflow-hidden whitespace-nowrap transition-[max-width,opacity,transform] duration-300 ' +
  (isOpen
    ? 'max-w-[8rem] opacity-100 translate-x-0'
    : 'max-w-0 opacity-0 -translate-x-2 pointer-events-none');

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
  (isActive
    ? 'bg-[var(--color-hebees-bg)] text-[var(--color-hebees)]'
    : 'text-gray-700 hover:bg-[var(--color-hebees)] hover:text-white');

export default function AdminLayout() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex">
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
              <Tooltip content="사이드바 열기" side="bottom" shiftX={15}>
                <button
                  onClick={() => setIsOpen(prev => !prev)}
                  className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-dark)]"
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
                className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-dark)]"
              >
                <Menu size={22} />
              </button>
            </Tooltip>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-2 mt-1 overflow-hidden">
          <NavLink to="/admin/dashboard" className={linkCls}>
            <Monitor size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">대시보드</span>
            </div>
          </NavLink>

          <NavLink to="/admin/documents" className={linkCls}>
            <FolderCog size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">문서 관리</span>
            </div>
          </NavLink>

          <NavLink to="/admin/chat" className={linkCls}>
            <MessageCirclePlus size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">새 채팅 시작하기</span>
            </div>
          </NavLink>

          <NavLink to="/admin/rag/settings" className={linkCls}>
            <Settings size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">RAG 모델 설정</span>
            </div>
          </NavLink>

          <NavLink to="/admin/rag/test" className={linkCls}>
            <Bot size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">RAG 모델 테스트</span>
            </div>
          </NavLink>
        </nav>

        <div className="mt-auto px-2 pb-4">
          <NavLink
            to="/logout"
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors text-gray-700 hover:bg-[var(--color-hebees-bg)] hover:text-[var(--color-hebees)]"
          >
            <LogOut size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">로그아웃</span>
            </div>
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <div className="sticky top-0 bg-transparent flex justify-end px-8 py-5">
          <Bell
            size={22}
            className="text-gray-600 hover:text-gray-800 cursor-pointer transition-colors shake-hover"
          />
        </div>
        <div className="flex w-full min-h-[calc(100vh-62px)] flex-col gap-3 px-8">
          <div className="flex-1 flex flex-col">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
