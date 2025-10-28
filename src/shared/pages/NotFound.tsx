import { NavLink } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="mx-auto max-w-lg rounded-xl border bg-white p-8 text-center">
      <div className="mb-2 text-2xl font-semibold">페이지를 찾을 수 없습니다</div>
      <p className="mb-6 text-sm text-gray-600">주소를 확인하거나 홈으로 돌아가세요.</p>
      <NavLink to="/login" className="rounded-md bg-gray-900 px-4 py-2 text-white">
        홈으로
      </NavLink>
    </div>
  );
}
