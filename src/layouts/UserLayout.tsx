import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Menu, MessageSquare, Image, FileText } from 'lucide-react';

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ' +
  (isActive ? 'bg-gray-900 text-white' : 'text-gray-700 hover:bg-gray-100');

export default function UserLayout() {
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
            <div className="text-lg font-semibold">User</div>
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
          <NavLink to="/user/chat/text" className={linkCls}>
            <MessageSquare size={18} />
            {isOpen && <span>텍스트 채팅</span>}
          </NavLink>
          <NavLink to="/user/chat/image" className={linkCls}>
            <Image size={18} />
            {isOpen && <span>이미지 채팅</span>}
          </NavLink>
          <NavLink to="/user/documents" className={linkCls}>
            <FileText size={18} />
            {isOpen && <span>내 문서</span>}
          </NavLink>
        </nav>
      </aside>
      <main className="flex-1 bg-gray-50 transition-all duration-300">
        <header className="sticky top-0 z-30 border-b bg-white px-6 py-4 text-sm text-gray-600">
          사용자 페이지
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
