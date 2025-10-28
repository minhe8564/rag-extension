import { useState } from 'react';
import { useNavigate, NavLink } from 'react-router-dom';
import HebeesGif from '@/assets/images/hebees-main.gif';
import Hebees from '@/assets/hebees-logo.webp';
import FormInput from '@/domains/auth/components/FormInput';
import UserTypeSelector from '@/domains/auth/components/UserTypeSelector';
import TermsModal from '@/domains/auth/components/TermsModal';

export default function Signup() {
  const nav = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [businessId, setBusinessId] = useState('');
  const [serviceName, setServiceName] = useState('');
  const [userType, setUserType] = useState('personal');
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      alert('비밀번호가 일치하지 않습니다.');
      return;
    }
    if (!agreeToTerms) {
      alert('서비스 이용약관에 동의해야 합니다.');
      return;
    }
    console.log('signup', { email, password, businessId, serviceName, userType, agreeToTerms });
    nav('/login', { replace: true });
  };

  const handleTermsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked && !agreeToTerms) {
      setIsModalOpen(true);
    } else {
      setAgreeToTerms(e.target.checked);
    }
  };

  const handleAgree = () => {
    setAgreeToTerms(true);
    setIsModalOpen(false);
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

      <div className="flex flex-col w-1/2 items-center justify-center bg-white space-y-14">
        <div className="flex flex-col items-center mb-6">
          <img src={Hebees} alt="logo" className="h-24 w-24 mb-3" />
          <p className="text-2xl text-gray-600 text-center leading-relaxed">
            <span
              className="font-semibold 
               bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
               bg-clip-text 
               text-transparent"
            >
              HEBEES RAG
            </span>{' '}
            와 함께,
            <br />더 똑똑한 대화를 시작해보세요!
          </p>
        </div>

        <form className="space-y-4 w-[50%]" onSubmit={onSubmit}>
          <FormInput
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            placeholder="이메일을 입력하세요."
            required
          />
          <FormInput
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="비밀번호를 입력하세요."
            required
          />
          <FormInput
            type="password"
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
            placeholder="비밀번호를 다시 입력하세요."
            required
          />
          <FormInput
            type="text"
            value={businessId}
            onChange={e => setBusinessId(e.target.value)}
            placeholder="사업자 번호를 입력하세요. (예:123-45-67890)"
          />
          <FormInput
            type="text"
            value={serviceName}
            onChange={e => setServiceName(e.target.value)}
            placeholder="서비스 사용 이름을 입력하세요."
          />
          <UserTypeSelector userType={userType} setUserType={setUserType} />
          <div className="flex items-center text-sm">
            <input
              type="checkbox"
              id="agreeTerms"
              className="h-4 w-4 text-[var(--color-hebees-blue)] rounded-sm focus:ring-[var(--color-hebees-blue)] border-gray-300"
              checked={agreeToTerms}
              onChange={handleTermsChange}
            />
            <label
              htmlFor="agreeTerms"
              className="ml-2 text-gray-600 cursor-pointer"
              onClick={() => setIsModalOpen(true)}
            >
              레티나 서비스 이용약관에 동의{' '}
              <span className="text-[var(--color-hebees-blue)] font-medium">(필수)</span>
            </label>
          </div>
          <button
            type="submit"
            className="w-full rounded-md bg-[var(--color-hebees-blue)] py-3 text-base font-medium text-white hover:brightness-95 transition-all"
            disabled={!agreeToTerms}
          >
            회원가입
          </button>
        </form>

        <div className="mt-6 text-center text-base text-gray-600">
          이미 가입된 계정이 있으신가요?{' '}
          <NavLink to="/login" className="text-[var(--color-hebees)] font-bold hover:underline">
            로그인
          </NavLink>
        </div>
      </div>
      <TermsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAgree={handleAgree}
      />
    </div>
  );
}
