import { useEffect, useState } from 'react';
import { springApi } from '@/shared/lib/apiInstance';
import { Loader2, UserCog, Mail, Shield, Building2, Hash, UserSquare2, Images } from 'lucide-react';
import ProfileInfoCard from '@/shared/components/ProfileInfoCard';
import ImageAlbum from '@/domains/user/components/image/ImageAlbum';
import FooterInfo from '@/shared/components/FooterInfo';
import KeyCard from '@/shared/components/ApiKey';

type UserInfo = {
  userNo: string;
  email: string;
  name: string;
  role: number; // 1: 사용자, 2: 관리자
  offerNo?: string; // 사업자 번호
  businessType?: number; // 0: 개인안경원, 1: 체인안경원, 2: 제조유통사
};

export default function Profile() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const { data } = await springApi.get<{ result: UserInfo }>('/api/v1/user/me');
        setUser(data.result);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMe();
  }, []);

  const getRoleLabel = (role: number) =>
    role === 2 ? '관리자' : role === 1 ? '사용자' : '알 수 없음';

  const getBusinessTypeLabel = (type?: number) =>
    type === 0 ? '개인안경원' : type === 1 ? '체인안경원' : type === 2 ? '제조유통사' : '-';

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 px-4 mb-20">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[var(--color-retina-bg)] flex items-center justify-center">
            <UserCog size={28} className="text-[var(--color-retina)]" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">내 정보</h1>
            <p className="text-sm text-gray-600">내 계정 정보를 확인하고 관리할 수 있습니다.</p>
          </div>
        </div>

        <div className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-10 text-gray-500">
              <Loader2 size={18} className="animate-spin mr-2" />
              정보를 불러오는 중입니다...
            </div>
          ) : user ? (
            <dl className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <ProfileInfoCard
                brand="retina"
                icon={<UserSquare2 size={20} strokeWidth={1.8} />}
                label="이름"
                value={<span className="text-base font-semibold text-gray-900">{user.name}</span>}
              />

              <ProfileInfoCard
                brand="retina"
                icon={<Mail size={20} strokeWidth={1.8} />}
                label="이메일"
                value={<span className="text-base font-medium text-gray-900">{user.email}</span>}
              />

              <ProfileInfoCard
                brand="retina"
                icon={<Shield size={20} strokeWidth={1.8} />}
                label="역할"
                value={
                  <span className="text-base font-medium text-gray-900">
                    {getRoleLabel(user.role)}
                  </span>
                }
              />

              <ProfileInfoCard
                brand="retina"
                icon={<Hash size={20} strokeWidth={1.8} />}
                label="사업자 번호"
                value={
                  <span className="text-base font-medium text-gray-800">{user.offerNo || '-'}</span>
                }
              />

              <ProfileInfoCard
                brand="retina"
                icon={<Building2 size={20} strokeWidth={1.8} />}
                label="사용자 유형"
                value={
                  <span className="text-base font-medium text-gray-900">
                    {getBusinessTypeLabel(user.businessType)}
                  </span>
                }
              />

              <div className="sm:col-span-1">
                <KeyCard brand="retina" />
              </div>
            </dl>
          ) : (
            <div className="py-10 text-center text-gray-500">
              사용자 정보를 불러오지 못했습니다.
            </div>
          )}
        </div>

        <section className="mb-20">
          <div className="mt-14 mb-4 flex items-center gap-4">
            <div className="p-3 rounded-xl bg-[var(--color-retina-bg)] flex items-center justify-center">
              <Images size={28} className="text-[var(--color-retina)]" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold">내 이미지 앨범</h1>
              <p className="text-sm text-gray-600">생성한 이미지를 한눈에 확인할 수 있습니다.</p>
            </div>
          </div>

          <ImageAlbum />
        </section>
      </main>

      <FooterInfo brand="hebees" />
    </div>
  );
}
