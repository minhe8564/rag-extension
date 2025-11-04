import { Outlet, NavLink, useLocation } from 'react-router-dom';

export default function PublicLayout() {
  const { pathname } = useLocation();

  if (pathname === '/login' || pathname === '/signup') {
    return <Outlet />;
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-800">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <NavLink to="/login" className="text-lg font-semibold">
            RAG Extension
          </NavLink>
          <nav className="flex gap-4 text-sm">
            <NavLink to="/login" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
              로그인
            </NavLink>
            <NavLink to="/signup" className={({ isActive }) => (isActive ? 'font-semibold' : '')}>
              회원가입
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10">
        <Outlet />
      </main>

      <footer className="mt-10 border-t bg-white">
        <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-gray-500">
          © {new Date().getFullYear()} RAG Extension
        </div>
      </footer>
    </div>
  );
}
