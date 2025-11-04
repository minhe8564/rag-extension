import { NavLink, useNavigate } from 'react-router-dom';
import HebeesLogo from '@/assets/hebees-logo.png';

const HOME_PATH = '/login';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col items-center bg-white text-gray-900">
      <main className="flex flex-col items-center w-full max-w-[720px] px-6 text-center justify-center flex-1">
        <h1 className="mb-4 text-4xl font-semibold tracking-tight md:text-5xl">404 ERROR</h1>
        <h3 className="mb-6 text-xl font-semibold tracking-tight md:text-3xl">
          페이지를 찾을 수 없습니다.
        </h3>

        <p className="mx-auto mb-10 max-w-[560px] text-sm leading-7 text-gray-600">
          <span className="block">죄송합니다. 페이지를 찾을 수 없습니다.</span>
          <span className="block">존재하지 않는 주소를 입력하셨거나,</span>
          <span className="block">요청하신 페이지의 주소가 변경·삭제되어 찾을 수 없습니다.</span>
        </p>

        <div className="mx-auto flex w-full max-w-[420px] items-center justify-center gap-3">
          <NavLink
            to={HOME_PATH}
            className="inline-flex flex-1 items-center justify-center rounded-md bg-[var(--color-hebees)] px-4 py-3 text-base font-medium text-white transition hover:opacity-90 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-black/10"
          >
            홈으로 가기
          </NavLink>

          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex flex-1 items-center justify-center rounded-md border border-gray-300 px-4 py-3 text-base font-medium text-gray-700 transition hover:bg-gray-50 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-black/5"
          >
            뒤로 돌아가기
          </button>
        </div>
      </main>

      <div className="mt-auto mb-8 flex justify-center">
        <img src={HebeesLogo} alt="hebees" className="w-40 h-9 object-contain" />
      </div>
    </div>
  );
}
