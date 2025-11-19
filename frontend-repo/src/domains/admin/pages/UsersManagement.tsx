import UsersListSection from '@/domains/admin/components/users/UsersListSection';
import RoleAsideSection from '@/domains/admin/components/users/RoleAsideSection';
import { Users } from 'lucide-react';

export default function UsersManagement() {
  return (
    <div className="space-y-8 px-4 mb-20">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-[var(--color-hebees-bg)] flex items-center justify-center">
          <Users size={28} className="text-[var(--color-hebees)]" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">
            <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
              HEBEES
            </span>{' '}
            <span className="font-semibold text-black">사용자 관리</span>
          </h1>
          <p className="text-sm text-gray-600">사용자 계정을 확인하고 관리할 수 있습니다.</p>
        </div>
      </div>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <UsersListSection />
        <RoleAsideSection />
      </section>
    </div>
  );
}
