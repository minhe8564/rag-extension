import { useEffect, useMemo, useState } from 'react';
import {
  getRoles,
  getRoleById,
  createRole,
  updateRole,
  deleteRole,
} from '@/domains/admin/api/roles.api';
import api from '@/shared/lib/apiInstance'; // users API는 아직 모듈화 전

// 백엔드 스펙에 맞춘 타입
type Role = {
  userRoleNo: string;
  mode: number; // 권한코드
  name: string; // 역할명
};

type UserItem = {
  userNo: number;
  email: string;
  nickname: string;
  role: string; // 서버가 roleKey 대신 role, name 대신 string 줄 경우
  status?: 'ACTIVE' | 'INACTIVE' | 'PENDING';
  createdAt?: string;
};

export default function Users() {
  // 사용자 상태
  const [users, setUsers] = useState<UserItem[]>([]);
  const [keyword, setKeyword] = useState('');
  const [filterRole, setFilterRole] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [loadingUsers, setLoadingUsers] = useState(false);

  // 역할 상태
  const [roles, setRolesState] = useState<Role[]>([]);
  const [activeRoleId, setActiveRoleId] = useState<string | null>(null);
  const [roleForm, setRoleForm] = useState<Partial<Role>>({
    name: '',
    mode: 0,
  });
  const [savingRole, setSavingRole] = useState(false);
  const [loadingRoles, setLoadingRoles] = useState(false);

  // 초기 로드
  useEffect(() => {
    loadRoles();
    loadUsers();
  }, []);

  // 역할 로드
  const loadRoles = async () => {
    try {
      setLoadingRoles(true);
      const list = await getRoles();
      setRolesState(list);
    } catch (e) {
      console.error('roles load error', e);
    } finally {
      setLoadingRoles(false);
    }
  };

  // 사용자 로드
  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const { data } = await api.get('/users', {
        params: {
          q: keyword || undefined,
          role: filterRole !== 'ALL' ? filterRole : undefined,
          status: filterStatus !== 'ALL' ? filterStatus : undefined,
        },
      });
      setUsers(data.result || []);
    } finally {
      setLoadingUsers(false);
    }
  };

  // 역할 선택(폼 채우기)
  const selectRole = async (role: Role) => {
    setActiveRoleId(role.userRoleNo);

    const detail = await getRoleById(role.userRoleNo);

    setRoleForm({
      name: detail.name,
      mode: detail.mode,
    });
  };

  // 새 역할
  const resetRoleForm = () => {
    setActiveRoleId(null);
    setRoleForm({ name: '', mode: 0 });
  };

  // 역할 저장
  const handleSaveRole = async () => {
    if (!roleForm.name) return alert('역할명을 입력해주세요.');

    try {
      setSavingRole(true);

      if (!activeRoleId) {
        await createRole({
          name: roleForm.name!,
          mode: Number(roleForm.mode),
        });
      } else {
        await updateRole(activeRoleId, {
          name: roleForm.name!,
          mode: Number(roleForm.mode),
        });
      }

      await loadRoles();
      resetRoleForm();
    } catch (err) {
      console.error('role save fail', err);
      alert('역할 저장 실패');
    } finally {
      setSavingRole(false);
    }
  };

  // 역할 삭제
  const handleDeleteRole = async (id: string) => {
    if (!confirm('해당 역할을 삭제할까요?')) return;

    await deleteRole(id);
    if (activeRoleId === id) resetRoleForm();
    await loadRoles();
  };

  // 필터 적용된 사용자 목록
  const filteredUsers = useMemo(() => {
    let list = [...users];

    if (filterRole !== 'ALL') list = list.filter(u => u.role === filterRole);

    if (filterStatus !== 'ALL') list = list.filter(u => (u.status || 'ACTIVE') === filterStatus);

    if (keyword.trim()) {
      const k = keyword.toLowerCase();
      list = list.filter(u => `${u.email}${u.nickname || ''}`.toLowerCase().includes(k));
    }

    return list;
  }, [users, keyword, filterRole, filterStatus]);

  return (
    <div className="space-y-8 px-4 mb-20">
      <h1 className="text-2xl">
        <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
          HEBEES
        </span>{' '}
        <span className="font-semibold text-black">사용자 관리</span>
      </h1>

      {/* 사용자 리스트 + 역할 리스트 */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        {/* 사용자 목록 */}
        <div className="space-y-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
            <div className="flex gap-2">
              <input
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                placeholder="이메일/닉네임 검색"
                className="w-56 rounded-md border px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[var(--color-hebees)]"
              />
              <button
                onClick={loadUsers}
                className="rounded-md bg-[var(--color-hebees)] px-3 py-2 text-sm text-white"
              >
                검색
              </button>
            </div>

            <div className="flex gap-2">
              <select
                value={filterRole}
                onChange={e => setFilterRole(e.target.value)}
                className="rounded-md border px-3 py-2 text-sm"
              >
                <option value="ALL">전체 역할</option>
                {roles.map(r => (
                  <option key={r.userRoleNo} value={r.name}>
                    {r.name}
                  </option>
                ))}
              </select>
              <select
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                className="rounded-md border px-3 py-2 text-sm"
              >
                <option value="ALL">전체 상태</option>
                <option value="ACTIVE">활성</option>
                <option value="INACTIVE">비활성</option>
                <option value="PENDING">대기</option>
              </select>
            </div>
          </div>

          {/* 사용자 테이블 */}
          <div className="rounded-xl border bg-white overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-[var(--color-hebees-bg)] text-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left">이메일</th>
                  <th className="px-4 py-3 text-left">닉네임</th>
                  <th className="px-4 py-3 text-left">역할</th>
                  <th className="px-4 py-3 text-left">상태</th>
                  <th className="px-4 py-3 text-right">가입일</th>
                </tr>
              </thead>
              <tbody>
                {loadingUsers ? (
                  <tr>
                    <td colSpan={5} className="text-center py-6">
                      불러오는 중...
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-6 text-gray-500">
                      없음
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map(u => (
                    <tr key={u.userNo} className="border-t">
                      <td className="px-4 py-3">{u.email}</td>
                      <td className="px-4 py-3">{u.nickname || '-'}</td>
                      <td className="px-4 py-3">{u.role}</td>
                      <td className="px-4 py-3">{u.status}</td>
                      <td className="px-4 py-3 text-right text-gray-500">
                        {u.createdAt ? new Date(u.createdAt).toLocaleDateString() : '-'}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* 역할 리스트 */}
        <aside className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold">역할 목록</h2>
            <button className="border px-2 py-1 text-xs rounded-md" onClick={loadRoles}>
              새로고침
            </button>
          </div>

          <div className="rounded-xl border bg-white p-2 space-y-2">
            {loadingRoles ? (
              <div className="p-4 text-center text-sm text-gray-500">불러오는 중…</div>
            ) : (
              roles.map(r => (
                <div
                  key={r.userRoleNo}
                  className={`flex justify-between items-center px-3 py-2 rounded-lg cursor-pointer hover:bg-[var(--color-hebees-bg)] 
                ${activeRoleId === r.userRoleNo ? 'bg-[var(--color-hebees-bg)]' : ''}`}
                >
                  <button onClick={() => selectRole(r)} className="flex flex-col text-left">
                    <span className="font-medium">{r.name}</span>
                    <span className="text-xs text-gray-500">mode: {r.mode}</span>
                  </button>
                  <button
                    onClick={() => handleDeleteRole(r.userRoleNo)}
                    className="text-xs text-gray-500 border px-2 py-1 rounded opacity-0 group-hover:opacity-100"
                  >
                    삭제
                  </button>
                </div>
              ))
            )}
          </div>

          <button className="border rounded-lg px-3 py-2 w-full" onClick={resetRoleForm}>
            새 역할 만들기
          </button>
        </aside>
      </section>

      {/* 역할 폼 */}
      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <h2 className="text-base font-semibold">
            {activeRoleId ? `역할 수정 (#${activeRoleId})` : '역할 생성'}
          </h2>

          <div className="rounded-xl border bg-white p-4 space-y-4">
            <div>
              <label className="text-xs text-gray-500">역할명(name)</label>
              <input
                value={roleForm.name || ''}
                onChange={e => setRoleForm(v => ({ ...v, name: e.target.value }))}
                className="w-full border rounded-md px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="text-xs text-gray-500">모드(mode)</label>
              <input
                type="number"
                value={roleForm.mode ?? 0}
                onChange={e => setRoleForm(v => ({ ...v, mode: Number(e.target.value) }))}
                className="w-full border rounded-md px-3 py-2 text-sm"
              />
            </div>

            <div className="flex justify-end gap-2">
              <button className="border px-4 py-2 rounded-md text-sm" onClick={resetRoleForm}>
                초기화
              </button>
              <button
                className="bg-[var(--color-hebees)] text-white px-4 py-2 rounded-md text-sm"
                disabled={savingRole}
                onClick={handleSaveRole}
              >
                {savingRole ? '저장 중...' : '저장'}
              </button>
            </div>
          </div>
        </div>

        <aside>
          <div className="border rounded-xl p-4 text-sm bg-white">
            <b>권한 관리 가이드</b>
            <ul className="list-disc pl-4 mt-2 space-y-1">
              <li>역할명(name)은 고유해야 합니다.</li>
              <li>mode는 권한 레벨입니다. (예: 0=USER, 1=ADMIN)</li>
              <li>삭제 전 역할이 배정된 사용자가 없는지 확인하세요.</li>
            </ul>
          </div>
        </aside>
      </section>
    </div>
  );
}
