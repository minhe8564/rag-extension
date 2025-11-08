import { DatabaseZap } from 'lucide-react';

export default function PageHeader() {
  return (
    <>
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-gradient-to-r from-[#EED8F3]/70 to-[#CBE1FF]/70 flex items-center justify-center shadow-sm backdrop-blur-sm">
          <DatabaseZap size={26} className="text-[var(--color-hebees)]" />
        </div>

        <div>
          <h1 className="text-2xl mb-1 font-semibold">
            <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
              HEBEES RAG
            </span>{' '}
            <span className="font-semibold text-black">대시보드</span>
          </h1>

          <p className="text-sm text-gray-600">
            문서 임베딩 상태와 검색 품질 지표를 시각화해 분석하세요.
          </p>
        </div>
      </div>
    </>
  );
}
