import { useEffect, useMemo, useState } from 'react';
import { RotateCw } from 'lucide-react';
import { getUsers, type User } from '@/domains/admin/api/user.api';
import Pagination from '@/shared/components/Pagination';
import Select from '@/shared/components/Select';

export default function UsersListSection() {
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [filterRole, setFilterRole] = useState<string>('ALL');
  const [pageNum, setPageNum] = useState(1);
  const pageSize = 10;

  const roleOptions = [
    { label: '전체 역할', value: 'ALL' },
    { label: '사용자', value: '1' },
    { label: '관리자', value: '2' },
  ];

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const result = await getUsers({ pageSize: 9999 }); // 전체 유저 가져오기
      setAllUsers(result.data);
    } finally {
      setLoading(false);
    }
  };

  // ✅ 필터 + 검색 + 페이지 적용
  const filteredUsers = useMemo(() => {
    let filtered = [...allUsers];

    if (filterRole !== 'ALL') {
      filtered = filtered.filter(u => String(u.role) === filterRole);
    }

    if (keyword.trim()) {
      const lower = keyword.toLowerCase();
      filtered = filtered.filter(
        u => u.name.toLowerCase().includes(lower) || u.email.toLowerCase().includes(lower)
      );
    }

    return filtered;
  }, [allUsers, filterRole, keyword]);

  const totalPages = Math.ceil(filteredUsers.length / pageSize);
  const paginatedUsers = filteredUsers.slice((pageNum - 1) * pageSize, pageNum * pageSize);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">사용자 목록</h2>

        <button
          className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm font-medium
            text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={loadUsers}
          disabled={loading}
        >
          <RotateCw
            size={16}
            strokeWidth={2}
            className={loading ? 'animate-spin text-gray-400' : 'text-gray-600'}
          />
          새로고침
        </button>
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-between">
        <div className="flex gap-2">
          <Select
            value={filterRole}
            onChange={v => {
              setFilterRole(v);
              setPageNum(1);
            }}
            options={roleOptions}
            placeholder="역할 선택"
            className="min-w-[180px] w-full"
          />
        </div>

        <div className="flex gap-2">
          <input
            value={keyword}
            onChange={e => {
              setKeyword(e.target.value);
              setPageNum(1);
            }}
            placeholder="이메일/이름 검색"
            className="w-56 rounded-md px-3 py-2 text-sm border border-gray-300 outline-none focus:border-[var(--color-hebees)] focus:bg-[var(--color-hebees-bg)] focus:ring-0"
          />
          <button
            onClick={() => setPageNum(1)}
            className="rounded-md bg-[var(--color-hebees)] px-3 py-2 text-sm text-white"
          >
            검색
          </button>
        </div>
      </div>

      <div className="rounded-xl border mt-4 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="text-gray-700 bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left">이메일</th>
              <th className="px-4 py-3 text-left">이름</th>
              <th className="px-4 py-3 text-left">역할</th>
              <th className="px-4 py-3 text-left">사업자번호</th>
              <th className="px-4 py-3 text-left">사업체 유형</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="text-center py-6">
                  불러오는 중...
                </td>
              </tr>
            ) : paginatedUsers.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-6 text-gray-500">
                  검색 결과가 없습니다.
                </td>
              </tr>
            ) : (
              paginatedUsers.map(u => (
                <tr key={u.userNo} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-3">{u.email}</td>
                  <td className="px-4 py-3">{u.name}</td>
                  <td className="px-4 py-3">{u.role === 1 ? '사용자' : '관리자'}</td>
                  <td className="px-4 py-3">{u.offerNo || '-'}</td>
                  <td className="px-4 py-3">
                    {u.businessType === 0
                      ? '개인 안경원'
                      : u.businessType === 1
                        ? '체인 안경원'
                        : '제조 유통사'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={pageNum}
        totalPages={totalPages}
        onPageChange={setPageNum}
        className="mt-4"
      />
    </div>
  );
}
