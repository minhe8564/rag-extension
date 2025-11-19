interface TermsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgree: () => void;
}

export default function TermsModal({ isOpen, onClose, onAgree }: TermsModalProps) {
  if (!isOpen) return null;

  const termsContent = (
    <div className="space-y-4 text-gray-700">
      <h3 className="text-lg font-medium text-[var(--color-hebees-blue)] text-center">
        레티나 서비스 이용약관
      </h3>
      <div className="h-64 overflow-y-auto border border-gray-200 p-4 rounded-md bg-gray-50 text-sm leading-relaxed">
        <p>
          **제 1조 (목적)**
          <br />본 약관은 [회사명] (이하 "회사")가 제공하는 레티나 서비스 및 관련 서비스(이하
          "서비스")의 이용에 관한 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.
        </p>
        <p className="mt-3">
          **제 2조 (약관의 효력 및 변경)**
          <br />
          ① 본 약관은 서비스를 이용하고자 하는 모든 이용자에 대하여 그 효력이 발생합니다.
          <br />② 회사는 합리적인 사유가 발생할 경우 관련 법령을 위배하지 않는 범위 내에서 본 약관을
          개정할 수 있습니다.
        </p>
        <p className="mt-3">
          **제 3조 (서비스 이용)**
          <br />
          이용자는 본 약관에 동의하는 경우 서비스를 이용할 수 있습니다. 이용자는 서비스 이용 시 관련
          법령을 준수해야 합니다.
        </p>
        <p className="mt-5 text-center font-semibold text-gray-600">
          ... 이하 생략. 상세 내용은 서비스 제공 페이지를 참고해 주십시오.
        </p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/70 flex justify-center items-center z-[9999]">
      <div className="bg-white rounded-lg shadow-2xl p-6 w-full max-w-2xl space-y-4">
        <h2 className="text-2xl font-bold text-center">이용약관 확인</h2>

        {termsContent}

        <div className="flex justify-center space-x-3 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
          >
            취소
          </button>
          <button
            type="button"
            onClick={onAgree}
            className="px-4 py-2 text-sm font-medium text-white bg-[var(--color-hebees-blue)] rounded-md hover:brightness-90 transition-all"
          >
            약관에 동의합니다
          </button>
        </div>
      </div>
    </div>
  );
}
