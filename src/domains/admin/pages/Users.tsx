import UsersListSection from '@/domains/admin/components/users/UsersListSection';
import RoleAsideSection from '@/domains/admin/components/users/RoleAsideSection';

export default function Users() {
  return (
    <div className="space-y-8 px-4 mb-20">
      <h1 className="text-2xl">
        <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
          HEBEES
        </span>{' '}
        <span className="font-semibold text-black">사용자 관리</span>
      </h1>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <UsersListSection />
        <RoleAsideSection />
      </section>
    </div>
  );
}
