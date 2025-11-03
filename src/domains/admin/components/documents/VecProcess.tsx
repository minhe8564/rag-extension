import { FileText, CloudUpload, Zap, Database, CircleCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import Pagination from '@/shared/components/Pagination';
import type { FileType } from '../../types';

export default function VecProcess({
  selectedFiles,
  initialFileName,
  initialCollection,
}: {
  selectedFiles: FileType[];
  initialFileName?: string;
  initialCollection?: string;
}) {
  // 외부에서 특정 파일로 진입 시 초기 인덱스 동기화
  useEffect(() => {
    if (!initialFileName) return;
    let idx = -1;
    if (initialCollection) {
      idx = selectedFiles.findIndex(
        (f) => f.name === initialFileName && (f.collection as string) === initialCollection
      );
    }
    if (idx < 0) {
      idx = selectedFiles.findIndex((f) => f.name === initialFileName);
    }
    if (idx >= 0) setCurrentIndex(idx);
  }, [initialFileName, initialCollection, selectedFiles]);
  const [currentIndex, setCurrentIndex] = useState(0);
  if (!selectedFiles || selectedFiles.length === 0) return null;

  const totalFiles = selectedFiles.length;
  const currentFile = selectedFiles[currentIndex];

  // 페이지네이션 이동
  const handlePageChange = (page: number) => setCurrentIndex(page - 1);

  return (
    <section className="border rounded-xl p-5 space-y-8 mt-6">
      <div className="flex justify-between items-center mb-4 border-b pb-2">
        {/* 오른쪽 페이지네이션 */}
        <Pagination
          page={currentIndex + 1}
          totalPages={totalFiles}
          onPageChange={handlePageChange}
        />
      </div>

      <div key={currentFile.name} className="border rounded-lg p-4 shadow-sm">
        {/* 파일 헤더 */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-7 h-7 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
            <FileText size={17} className="text-[var(--color-white)]" />
          </div>
          <h3 className="text-xs font-semibold">{currentFile.name}</h3>
        </div>

        {/* 단계별 진행 아이콘 */}
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
            <span className="text-xs text-gray-500">{currentFile.currentProgress ?? 0}%</span>
          </div>
        </div>

        {/* 진행률 바 */}
        <div className="space-y-2">
          {[
            { label: 'minIO 업로드', percent: 100 },
            { label: '데이터 정제', percent: 100 },
            { label: '임베딩 생성', percent: 100 },
          ].map((step, i) => (
            <div key={i}>
              <p className="text-xs text-gray-700 mb-1">{step.label}</p>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] transition-all duration-700"
                  style={{ width: `${step.percent}%` }}
                />
              </div>
            </div>
          ))}

          {/* 전체 파일 처리 현황 */}
          <div className="mt-6 border-t border-gray-200 pt-4">
            <p className="text-xs text-gray-700 mb-1">전체 파일 처리 현황</p>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-[var(--color-retina)] transition-all duration-700"
                style={{ width: `${currentFile.totalProgress ?? 0}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
