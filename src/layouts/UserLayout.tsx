import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { Menu, MessageSquare, Image, FolderCog, LogOut, Bell } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import RetinaLogo from '@/assets/retina-logo.png';

const labelCls = (isOpen: boolean) =>
  'ml-2 overflow-hidden whitespace-nowrap transition-[max-width,opacity,transform] duration-300 ' +
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

  return (
    <div className="flex min-h-screen">
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
                  onClick={() => setIsOpen(prev => !prev)}
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
              <span className="inline-block">텍스트 채팅</span>
            </div>
          </NavLink>

          <NavLink to="/user/chat/image" className={linkCls}>
            <Image size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">이미지 채팅</span>
            </div>
          </NavLink>

          <NavLink to="/user/documents" className={linkCls}>
            <FolderCog size={18} className="flex-shrink-0" />
            <div className={labelCls(isOpen)}>
              <span className="inline-block">내 문서 관리</span>
            </div>
          </NavLink>
        </nav>

        <div className="mt-auto px-2 pb-4">
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
        <div className="sticky top-0 bg-transparent flex justify-end px-8 py-5">
          <Bell
            size={22}
            className="text-gray-600 hover:text-gray-800 cursor-pointer transition-colors shake-hover"
          />
        </div>
        <div className="flex flex-col w-full gap-3 px-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
