import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { FileText, CloudUpload, Zap, Database, CircleCheck } from 'lucide-react';
import type { RawMyDoc } from '@/shared/types/file.types';
import type { VectorizationItem } from '@/domains/admin/types/documents.types';
import { getVectorizationProgress } from '@/domains/admin/api/documents.api';
import Pagination from '@/shared/components/Pagination';

type VecProcessProps = {
  selectedFiles: RawMyDoc[];
  isVectorizingDone: boolean;
  onVectorizationComplete?: () => void;
};

type FileState = {
  progress: number;
  status: VectorizationItem['status'];
  step: VectorizationItem['currentStep'];
};

export default function VecProcess({
  selectedFiles,
  isVectorizingDone,
  onVectorizationComplete,
}: VecProcessProps) {
  const [fileStates, setFileStates] = useState<Record<string, FileState>>({});
  const [overallStatus, setOverallStatus] = useState<'IDLE' | 'RUNNING' | 'DONE' | 'ERROR'>('IDLE');
  const [currentIndex, setCurrentIndex] = useState(0);

  const totalFiles = selectedFiles.length;
  const currentFile = selectedFiles[currentIndex];

  //  최초 조회
  const { data: initialData } = useQuery({
    queryKey: ['vectorization-progress'],
    queryFn: () => getVectorizationProgress(),
    staleTime: 1000 * 30,
    refetchOnWindowFocus: false,
  });

  //  초기 데이터 세팅
  useEffect(() => {
    if (!initialData) return;

    const init: Record<string, FileState> = {};
    initialData.items.forEach((item: VectorizationItem) => {
      init[item.docName] = {
        progress: item.overallPct ?? 0,
        status: item.status,
        step: item.currentStep,
      };
    });

    setFileStates(init);
    setOverallStatus('RUNNING');
  }, [initialData]);

  //  SSE 실시간 진행률 반영
  useEffect(() => {
    if (!isVectorizingDone || selectedFiles.length === 0) return;

    const eventSource = new EventSourcePolyfill('/api/v1/ingest/progress');

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const items = data.items ?? [];

        const updated: Record<string, FileState> = {};
        items.forEach((item: VectorizationItem) => {
          updated[item.docName] = {
            progress: item.overallPct ?? 0,
            status: item.status,
            step: item.currentStep,
          };
        });

        setFileStates((prev) => ({ ...prev, ...updated }));

        const allDone = items.every((i: VectorizationItem) => i.status === 'COMPLETED');
        if (allDone) {
          setOverallStatus('DONE');
          onVectorizationComplete?.();
          eventSource.close();
        }
      } catch (err) {
        console.error('SSE 데이터 파싱 실패', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE 연결 오류 발생', err);
      setOverallStatus('ERROR');
      eventSource.close();
    };

    return () => eventSource.close();
  }, []);

  const handlePageChange = (newIndex: number) => {
    setCurrentIndex(newIndex - 1);
  };

  const currentFileState = fileStates[currentFile?.name] ?? {
    progress: 0,
    status: 'PENDING',
    step: null,
  };

  return (
    <section className="border rounded-xl p-5 space-y-8 mt-6">
      {/* 상단: 페이지네이션 */}
      <div className="flex justify-between items-center mb-4 border-b pb-2">
        <Pagination
          pageNum={currentIndex + 1}
          totalPages={totalFiles}
          onPageChange={(newPage) => handlePageChange(newPage)}
          hasPrev={currentIndex > 0}
          hasNext={currentIndex < totalFiles - 1}
        />
      </div>

      {/* 현재 파일 진행상황 */}
      {currentFile && (
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
            {[
              { icon: CloudUpload, label: 'minIO 업로드', step: 'UPLOAD' },
              { icon: Zap, label: '데이터 정제', step: 'CLEAN' },
              { icon: Database, label: '임베딩 생성', step: 'EMBED' },
              { icon: CircleCheck, label: 'Vector DB 저장', step: 'UPSERT' },
            ].map(({ icon: Icon, label, step }) => {
              const isActive = currentFileState.step === step;
              const percent =
                currentFileState.progress >= 100
                  ? 100
                  : currentFileState.step === step
                    ? currentFileState.progress
                    : currentFileState.progress;

              return (
                <div key={label} className="flex flex-col items-center">
                  <Icon
                    className={`w-12 h-12 ${
                      isActive
                        ? 'text-[var(--color-hebees)]'
                        : 'text-[var(--color-hebees-blue)] opacity-60'
                    }`}
                  />
                  <span className="text-sm font-medium text-gray-700 mt-1">{label}</span>
                  <span className="text-xs text-gray-500">{percent.toFixed(1)}%</span>
                </div>
              );
            })}
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
                  style={{
                    width: `${currentFileState.progress ?? 0}%`,
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 상태 표시 */}
      <div className="mt-3 text-center text-sm text-gray-600">
        {overallStatus === 'RUNNING' && '벡터화가 진행 중입니다...'}
        {overallStatus === 'DONE' && '벡터화가 완료되었습니다!'}
        {overallStatus === 'ERROR' && '일부 벡터화에 실패했습니다.'}
      </div>
    </section>
  );
}
