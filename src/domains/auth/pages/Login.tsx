import { useState } from 'react';
import { useNavigate, useLocation, NavLink } from 'react-router-dom';
import HebeesGif from '@/assets/images/hebees-main.gif';
import Hebees from '@/assets/hebees-logo.webp';
import { Eye, EyeOff } from 'lucide-react';

export default function Login() {
  const nav = useNavigate();
  const location = useLocation() as any;
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const from = location.state?.from?.pathname || '/user/documents';

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('login', { email, password });
    nav(from, { replace: true });
  };

  const togglePasswordVisibility = (
    setter: React.Dispatch<React.SetStateAction<boolean>>,
    current: boolean
  ) => {
    setter(!current);
  };

  return (
    <div className="flex min-h-screen bg-[var(--color-retina-bg)]">
      <div className="flex w-1/2 flex-col items-center justify-center bg-[var(--color-main)] text-center relative overflow-hidden">
        <img
          src={HebeesGif}
          alt="hebees animation"
          className="absolute top-1/2 left-1/2 w-50px -translate-x-1/2 -translate-y-1/2"
        />
      </div>

      <div className="flex flex-col w-1/2 items-center justify-center bg-white space-y-20">
        <div className="flex flex-col items-center mb-6">
          <img src={Hebees} alt="logo" className="h-24 w-24 mb-3" />
          <p className="text-2xl text-gray-600 text-center leading-relaxed">
            <span
              className="font-bold
             bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text 
             text-transparent"
            >
              HEBEES RAG
            </span>{' '}
            와 함께,
            <br />더 똑똑한 데이터를 시작해보세요!
          </p>
        </div>

        <form className="space-y-4 w-[60%]" onSubmit={onSubmit}>
          <div>
            <input
              className="w-full rounded-md border border-gray-300 p-3 text-sm outline-none focus:border-[var(--color-hebees-blue)] focus:bg-[var(--color-hebees-blue-bg)]"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="이메일"
              required
            />
          </div>
          <div className="relative">
            <input
              className="w-full rounded-md border border-gray-300 p-3 text-sm outline-none focus:border-[var(--color-hebees-blue)] focus:bg-[var(--color-hebees-blue-bg)]"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="비밀번호"
              required
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
              onClick={() => togglePasswordVisibility(setShowConfirmPassword, showConfirmPassword)}
              aria-label={showConfirmPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
            >
              {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button
            type="submit"
            className="w-full rounded-md bg-[var(--color-hebees-blue)] py-3 text-base font-medium text-white hover:brightness-95 transition-all"
          >
            로그인
          </button>
        </form>

        <div className="mt-6 text-center text-base text-gray-600">
          아직 가입된 계정이 없으신가요?{' '}
          <NavLink to="/signup" className="text-[var(--color-hebees)] font-bold hover:underline">
            회원가입
          </NavLink>
        </div>
      </div>
    </div>
  );
}
