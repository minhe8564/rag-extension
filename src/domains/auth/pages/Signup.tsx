import { useState } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';

export default function Signup() {
  const nav = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // 회원가입 연동
    console.log('signup', { email, password, nickname });
    nav('/login', { replace: true });
  };

  return (
    <div className="mx-auto max-w-md rounded-xl border bg-white p-6 shadow-sm">
      <h1 className="mb-2 text-xl font-semibold">회원가입</h1>
      <p className="mb-6 text-sm text-gray-500">정보를 입력해 계정을 생성하세요.</p>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div>
          <label className="mb-1 block text-sm text-gray-600">닉네임</label>
          <input
            className="w-full rounded-md border px-3 py-2 focus:ring"
            value={nickname}
            onChange={e => setNickname(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-600">이메일</label>
          <input
            className="w-full rounded-md border px-3 py-2 focus:ring"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-600">비밀번호</label>
          <input
            className="w-full rounded-md border px-3 py-2 focus:ring"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="w-full rounded-md bg-gray-900 px-4 py-2 text-white">
          가입하기
        </button>
      </form>
      <div className="mt-4 text-center text-sm">
        이미 계정이 있나요?{' '}
        <NavLink to="/login" className="text-gray-900 underline">
          로그인
        </NavLink>
      </div>
    </div>
  );
}
