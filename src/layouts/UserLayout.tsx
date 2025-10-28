import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Menu, MessageSquare, Image, FileText } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import RetinaLogo from '@/assets/retina-logo.png';

const linkCls = ({ isActive }: { isActive: boolean }) =>
  'flex items-center gap-3 rounded-md px-4 py-3 text-sm transition-colors ' +
  (isActive
    ? 'bg-[var(--color-retina)] text-white'
    : 'text-gray-700 hover:bg-[var(--color-retina-bg)] hover:text-[var(--color-retina)]');

export default function UserLayout() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="flex min-h-screen">
      <aside
        className={`flex flex-col bg-white transition-all duration-300 shadow-sm h-screen ${
          isOpen ? 'w-60 border-r' : 'w-16 border-r'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-6">
          {isOpen ? (
            <div className="text-lg font-semibold">
              <img src={RetinaLogo} alt="Retina" className="w-30 h-10 object-contain" />
            </div>
          ) : (
            <div className="w-full flex justify-center">
              <Tooltip content="사이드바 열기" side="bottom" shiftX={15}>
                <button
                  onClick={() => setIsOpen(prev => !prev)}
                  className="text-[var(--color-retina)] hover:text-[var(--color-retina-dark)]"
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
                className="text-[var(--color-retina)] hover:text-[var(--color-retina-dark)]"
              >
                <Menu size={24} />
              </button>
            </Tooltip>
          )}
        </div>

        <nav className="flex flex-col gap-1 px-2">
          <NavLink to="/user/chat/text" className={linkCls}>
            <MessageSquare size={20} />
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
