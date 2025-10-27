import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Menu, Settings, Monitor, FolderCog, MessageCirclePlus, Bot} from 'lucide-react';
import  hebesslogo  from '@/assets/hebesslogo.png';

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
  (isActive ? 'bg-[var(--color-hebees)] text-white' : 'text-gray-700 hover:bg-[var(--color-hebees-bg)] hover:text-[var(--color-hebees)]');

export default function AdminLayout() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      <aside
        className={`flex flex-col bg-white transition-all duration-300 shadow-sm h-screen ${
          isOpen ? 'w-60 border-r' : 'w-16 border-r'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-4">
          {isOpen ? (
            <div className="text-lg font-semibold"><img src={hebesslogo} alt="hebesslogo" className="w-24 h-12 object-contain" /></div>
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

        <nav className="flex flex-col gap-1 px-2">
          <NavLink to="/admin/dashboard" className={linkCls}>
            <Monitor size={18} />
            {isOpen && <span>대시보드</span>}
          </NavLink>

          <NavLink to="/admin/documents" className={linkCls}>
            <FolderCog size={18} />
            {isOpen && <span>문서 관리</span>}
          </NavLink>

          <NavLink to="/admin/chat" className={linkCls}>
            <MessageCirclePlus size={18} />
            {isOpen && <span>새 채팅 시작하기</span>}
          </NavLink>

          <NavLink to="/admin/rag/settings" className={linkCls}>
            <Settings size={18} />
            {isOpen && <span>RAG 설정</span>}
          </NavLink>

          <NavLink to="/admin/rag/test" className={linkCls}>
            <Bot size={18} />
            {isOpen && <span>RAG 테스트</span>}
          </NavLink>
        </nav>
      </aside>

      <main className="flex-1 bg-gray-50 transition-all duration-300">
        <header className="sticky top-0 z-30 border-b bg-white px-6 py-4 text-sm text-gray-600">
          관리자 페이지
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
