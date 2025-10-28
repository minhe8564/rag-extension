import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Menu, Settings, Monitor, FolderCog, MessageCirclePlus, Bot, Bell } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import HebeesLogo from '@/assets/hebees-logo.png';

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-3 text-base transition-colors ' +
  (isActive
    ? 'bg-[var(--color-hebees-bg)] text-[var(--color-hebees)]'
    : 'text-gray-700 hover:bg-[var(--color-hebees)] hover:text-white');

export default function AdminLayout() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      <aside
        className={`flex flex-col bg-white transition-all duration-300 shadow-sm h-screen ${
          isOpen ? 'w-72 border-r' : 'w-[72px] border-r'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-6">
          {isOpen ? (
            <div className="text-lg font-semibold">
              <img src={HebeesLogo} alt="Hebees" className="w-30 h-10 object-contain" />
            </div>
          ) : (
            <div className="w-full flex justify-center">
              <Tooltip content="사이드바 열기" side="bottom" shiftX={15}>
                <button
                  onClick={() => setIsOpen(prev => !prev)}
                  className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-dark)]"
                >
                  <Menu size={24} />
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
                <Menu size={24} />
              </button>
            </Tooltip>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-2 mt-2 overflow-hidden whitespace-nowrap">
          <NavLink to="/admin/dashboard" className={linkCls}>
            <Monitor size={20} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">대시보드</span>
            </div>
          </NavLink>

          <NavLink to="/admin/documents" className={linkCls}>
            <FolderCog size={20} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">문서 관리</span>
            </div>
          </NavLink>

          <NavLink to="/admin/chat" className={linkCls}>
            <MessageCirclePlus size={20} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">새 채팅 시작하기</span>
            </div>
          </NavLink>

          <NavLink to="/admin/rag/settings" className={linkCls}>
            <Settings size={20} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">RAG 모델 설정</span>
            </div>
          </NavLink>

          <NavLink to="/admin/rag/test" className={linkCls}>
            <Bot size={18} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">RAG 모델 테스트</span>
            </div>
          </NavLink>
        </nav>
      </aside>

      <main className="flex-1 transition-all duration-300">
        <div className="flex flex-col gap-4 px-32">
          <Bell
            size={24}
            className="self-end text-gray-600 hover:text-gray-800 cursor-pointer transition-colors shake-hover mt-10"
          />
          <Outlet />
        </div>
      </main>
    </div>
  );
}
