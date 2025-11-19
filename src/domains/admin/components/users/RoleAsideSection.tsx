import { useEffect, useState } from 'react';
import {
  getRoles,
  getRoleById,
  createRole,
  updateRole,
  deleteRole,
} from '@/domains/admin/api/roles.api';
import { RefreshCw, Trash2 } from 'lucide-react';
import Tooltip from '@/shared/components/controls/Tooltip';
import ConfirmModal from '@/shared/components/ConfirmModal';
import { Loader2 } from 'lucide-react';

type Role = {
  uuid: string;
  mode: number | null;
  name: string;
};

const ROLE_NAME_MAX = 30;
const ROLE_MODE_MAX = 100;

export default function RoleAsideSection() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [activeRoleId, setActiveRoleId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Partial<Role>>({ name: '', mode: 0 });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingRole, setPendingRole] = useState<Role | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadRoles();
  }, []);

  const loadRoles = async () => {
    try {
      setLoading(true);
      const list = await getRoles();
      setRoles(list);
    } finally {
      setLoading(false);
    }
  };

  const selectRole = async (role: Role) => {
    setActiveRoleId(role.uuid);
    setShowForm(true);
    const detail = await getRoleById(role.uuid);
    setForm({ name: detail.name, mode: detail.mode });
  };

  const resetForm = () => {
    setActiveRoleId(null);
    setForm({ name: '', mode: 0 });
    setShowForm(false);
  };

  const saveRole = async () => {
    if (!form.name) return alert('역할명을 입력해주세요.');
    try {
      setSaving(true);
      if (activeRoleId) {
        await updateRole(activeRoleId, { name: form.name!, mode: form.mode! });
      } else {
        await createRole({ name: form.name!, mode: form.mode! });
      }
      await loadRoles();
      resetForm();
    } finally {
      setSaving(false);
    }
  };

  const removeRole = async (id: string) => {
    setDeleting(true);
    try {
      await deleteRole(id);
      if (activeRoleId === id) resetForm();
      await loadRoles();
    } finally {
      setDeleting(false);
    }
  };

  const handleRequestDelete = (role: Role) => {
    setPendingRole(role);
    setConfirmOpen(true);
  };

  const handleCloseConfirm = () => {
    setConfirmOpen(false);
    setPendingRole(null);
  };

  const handleConfirmDelete = async () => {
    if (!pendingRole) return;
    await removeRole(pendingRole.uuid);
    handleCloseConfirm();
  };

  return (
    <aside className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold">역할 목록</h2>
        <button
          className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm font-medium
               text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          onClick={loadRoles}
        >
          <RefreshCw size={16} strokeWidth={2} />
          새로고침
        </button>
      </div>

      <div className="rounded-xl border bg-white p-2 space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <Loader2 size={18} className="mr-2 animate-spin" />
            불러오는 중…
          </div>
        ) : (
          roles.map((r) => (
            <div
              key={r.uuid}
              className={`group flex justify-between items-center px-3 py-2 rounded-lg cursor-pointer hover:bg-[var(--color-hebees-bg)] ${
                activeRoleId === r.uuid ? 'bg-[var(--color-hebees-bg)]' : ''
              }`}
            >
              <button onClick={() => selectRole(r)} className="flex flex-col text-left">
                <span className="font-medium">{r.name}</span>
                <span className="text-xs text-gray-500">mode: {r.mode}</span>
              </button>

              <Tooltip content="삭제" side="bottom">
                <button
                  type="button"
                  onClick={() => handleRequestDelete(r)}
                  disabled={deleting}
                  className="
                    flex items-center gap-1 text-sm text-gray-600 px-1.5 py-1.5 rounded-md
                    bg-white opacity-0 group-hover:opacity-100
                    hover:bg-gray-100 hover:text-gray-800
                    transition
                  "
                >
                  <Trash2 size={16} strokeWidth={2} />
                </button>
              </Tooltip>
            </div>
          ))
        )}
      </div>

      <button className="border rounded-lg px-3 py-2 w-full" onClick={() => setShowForm(true)}>
        새 역할 만들기
      </button>

      {showForm && (
        <div className="rounded-xl border bg-white p-4 space-y-4 mt-3">
          <h3 className="text-base font-semibold">
            {activeRoleId ? `역할 수정 (#${activeRoleId})` : '역할 생성'}
          </h3>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-500">역할명(name)</label>
              <input
                value={form.name || ''}
                onChange={(e) =>
                  setForm((v) => ({
                    ...v,
                    name: e.target.value.slice(0, ROLE_NAME_MAX),
                  }))
                }
                maxLength={ROLE_NAME_MAX}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-0 focus:border-gray-400"
              />
              <div className="mt-1 text-xs text-gray-400 text-right">
                {form.name?.length ?? 0}/{ROLE_NAME_MAX}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-500">모드(mode)</label>
              <input
                type="number"
                value={form.mode ?? 0}
                onChange={(e) => {
                  const n = Number(e.target.value);
                  const clamped = Math.min(isNaN(n) ? 0 : n, ROLE_MODE_MAX);
                  setForm((v) => ({ ...v, mode: clamped }));
                }}
                max={ROLE_MODE_MAX}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm
                           focus:outline-none focus:ring-0 focus:border-gray-400"
              />
              <div className="mt-1 text-xs text-gray-400 text-right">
                최대 {ROLE_MODE_MAX} 까지 입력 가능
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <button className="border px-4 py-2 rounded-md text-sm" onClick={resetForm}>
              취소
            </button>
            <button
              className="bg-[var(--color-hebees)] text-white px-4 py-2 rounded-md text-sm"
              disabled={saving}
              onClick={saveRole}
            >
              {saving ? '저장 중...' : '저장'}
            </button>
          </div>

          <div className="border-t pt-3 mt-3 text-sm text-gray-600">
            <b className="block mb-1">권한 관리 가이드</b>
            <ul className="list-disc pl-4 space-y-1">
              <li>역할명(name)은 고유해야 합니다.</li>
              <li>mode는 권한 레벨입니다. (예: 0=USER, 1=ADMIN)</li>
              <li>삭제 전 역할이 배정된 사용자가 없는지 확인하세요.</li>
            </ul>
          </div>
        </div>
      )}

      <ConfirmModal
        open={confirmOpen}
        onClose={handleCloseConfirm}
        onConfirm={handleConfirmDelete}
        title="역할 삭제"
        message={
          pendingRole
            ? `정말로 이 역할을 삭제할까요?\n"${pendingRole.name}"`
            : '정말로 이 역할을 삭제할까요?'
        }
        confirmText={deleting ? '삭제 중...' : '삭제'}
        cancelText="취소"
        variant="danger"
        zIndex={10060}
      />
    </aside>
  );
}
