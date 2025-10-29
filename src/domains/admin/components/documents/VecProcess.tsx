import { FileText, CloudUpload, Zap, Database, CircleCheck } from 'lucide-react';

interface VecProcessProps {
  selectedFile: {
    id: number;
    name: string;
    size: string;
    category: string;
    storage: string;
    currentProgress: string;
    totalProgress: number;
  } | null;
}
export default function VecProcess({ selectedFile }: VecProcessProps) {
  if (!selectedFile) return null;
  return (
    <section className="border rounded-xl p-5">
      <div
        className={`flex items-center justify-center gap-2 mb-8 min-h-[30px] transition-all ${
          selectedFile ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <div className="w-7 h-7 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
          <FileText size={17} className="text-[var(--color-white)]" />
        </div>
        <h3 className="text-xs">{selectedFile.name}</h3>
      </div>

      <div className="grid grid-cols-4 gap-6 mb-6">
        <div className="flex flex-col items-center">
          <CloudUpload className="w-12 h-12 text-[var(--color-hebees-blue)]" />
          <span className="text-sm font-medium text-gray-700 mt-1">minIO 업로드</span>
          <span className="text-xs text-gray-500">100%</span>
        </div>

        <div className="flex flex-col items-center">
          <Zap className="w-12 h-12 text-[var(--color-hebees-blue)]" />
          <span className="text-sm font-medium text-gray-700 mt-1">데이터 정제</span>
          <span className="text-xs text-gray-500">100%</span>
        </div>

        <div className="flex flex-col items-center">
          <Database className="w-12 h-12 text-[var(--color-hebees-blue)]" />
          <span className="text-sm font-medium text-gray-700 mt-1">임베딩 생성</span>
          <span className="text-xs text-gray-500">100%</span>
        </div>

        <div className="flex flex-col items-center">
          <CircleCheck className="w-12 h-12 text-[var(--color-hebees-blue)]" />
          <span className="text-sm font-medium text-gray-700 mt-1">Vector DB 저장</span>
          <span className="text-xs text-gray-500">{selectedFile.currentProgress}%</span>
        </div>
      </div>

      {/* 진행률 바 */}
      <div className="space-y-2">
        {[
          { label: 'minio 업로드', percent: 100 },
          { label: '데이터 정제', percent: 100 },
          { label: '임베딩 생성', percent: 100 },
        ].map((step, i) => (
          <div key={i}>
            <p className="text-xs text-gray-700 mb-1">{step.label}</p>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${'bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)]'} transition-all duration-700`}
                style={{ width: `${step.percent}%` }}
              />
            </div>
          </div>
        ))}
        <div className="mt-6 border-t border-gray-200 pt-4">
          <p className="text-xs text-gray-700 mb-1">전체 파일 처리 현황</p>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--color-retina)] transition-all duration-700"
              style={{ width: `$100%` }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
