import { useState } from 'react';
import { useNavigate, useLocation, NavLink } from 'react-router-dom';

export default function Login() {
  const nav = useNavigate();
  const location = useLocation() as any;
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const from = location.state?.from?.pathname || '/user/documents';

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // 로그인 연동
    console.log('login', { email, password });
    nav(from, { replace: true });
  };

  return (
    <div className="mx-auto max-w-md rounded-xl border bg-white p-6 shadow-sm">
      <h1 className="mb-2 text-xl font-semibold">로그인</h1>
      <p className="mb-6 text-sm text-gray-500">계정 정보를 입력하세요.</p>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div>
          <label className="mb-1 block text-sm text-gray-600">이메일</label>
          <input
            className="w-full rounded-md border px-3 py-2 outline-none focus:ring"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-600">비밀번호</label>
          <input
            className="w-full rounded-md border px-3 py-2 outline-none focus:ring"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>
        <button type="submit" className="w-full rounded-md bg-gray-900 px-4 py-2 text-white">
          로그인
        </button>
      </form>
      <div className="mt-4 text-center text-sm">
        계정이 없나요?{' '}
        <NavLink to="/signup" className="text-gray-900 underline">
          회원가입
        </NavLink>
      </div>
    </div>
  );
}
