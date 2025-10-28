import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Menu, Settings, Monitor, FolderCog, MessageCirclePlus, Bot, Bell } from 'lucide-react';
import hebesslogo from '@/assets/hebesslogo.png';

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
  (isActive
    ? 'bg-[var(--color-hebees)] text-white'
    : 'text-gray-700 hover:bg-[var(--color-hebees-bg)] hover:text-[var(--color-hebees)]');

export default function AdminLayout() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      <aside
        className={`flex flex-col bg-white transition-all duration-300 shadow-sm h-screen ${
          isOpen ? 'w-60 border-r' : 'w-16 border-r'
        }`}
      >
        <div className="flex items-center justify-between h-16 py-4 px-6">
          {isOpen ? (
            <div className="text-lg font-semibold">
              <img src={hebesslogo} alt="hebesslogo" className="w-24 h-8 object-contain" />
            </div>
          ) : (
            <div className="w-full flex justify-center">
              <button
                onClick={() => setIsOpen(prev => !prev)}
                className="text-gray-600 hover:text-gray-800"
              >
                <Menu size={20} />
              </button>
            </div>
          )}

          {isOpen && (
            <button onClick={() => setIsOpen(false)} className="text-gray-600 hover:text-gray-800">
              <Menu size={20} />
            </button>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-2 mt-2 overflow-hidden whitespace-nowrap">
          <NavLink to="/admin/dashboard" className={linkCls}>
            <Monitor size={18} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">대시보드</span>
            </div>
          </NavLink>

          <NavLink to="/admin/documents" className={linkCls}>
            <FolderCog size={18} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">문서 관리</span>
            </div>
          </NavLink>

          <NavLink to="/admin/chat" className={linkCls}>
            <MessageCirclePlus size={18} className="flex-shrink-0" />
            <div
              className={`transition-[width] duration-300 overflow-hidden ${
                isOpen ? 'w-32' : 'w-0'
              }`}
            >
              <span className="pl-2 inline-block">새 채팅 시작하기</span>
            </div>
          </NavLink>

          <NavLink to="/admin/rag/settings" className={linkCls}>
            <Settings size={18} className="flex-shrink-0" />
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
