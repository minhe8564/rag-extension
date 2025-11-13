// import { useState, useMemo } from 'react';
import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import PipelineFlow, {
  type FlowStep,
  //   type FlowStepId,
} from '@/shared/components/rag-pipeline/PipelineFlow';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';
import { getRagPipelineResponseTime } from '@/domains/admin/api/system.dashboard.api';
import type {
  RagPipelineResponseTimeMetric,
  RagPipelineResponseTimeResult,
} from '@/domains/admin/types/system.dashboard.types';
import clsx from 'clsx';

function msLabel(v?: number) {
  if (typeof v !== 'number') return '-';
  if (v < 1) return `${v.toFixed(2)} ms`;
  if (v < 10) return `${v.toFixed(1)} ms`;
  return `${Math.round(v)} ms`;
}

const normalizeKey = (s: string) => s.toLowerCase().replace(/\s+/g, '').replace(/-/g, '');

export default function RagResponseTime() {
  const { data, isLoading, isError } = useQuery<RagPipelineResponseTimeResult>({
    queryKey: ['admin', 'dashboard', 'rag', 'pipelineResponseTime'],
    queryFn: getRagPipelineResponseTime,
    staleTime: 30_000,
  });

  const metrics: RagPipelineResponseTimeMetric[] = useMemo(() => data?.metrics ?? [], [data]);

  const steps: FlowStep[] = useMemo(() => {
    const findMetric = (key: string): RagPipelineResponseTimeMetric | undefined =>
      metrics.find((m) => normalizeKey(m.name) === normalizeKey(key));

    const extract = findMetric('Extract');
    const chunk = findMetric('Chunking');
    const embed = findMetric('Embedding');
    const queryEmbed = findMetric('Query Embedding');
    const search = findMetric('Search');
    const crossEncoder = findMetric('Cross Encoder');
    const gen = findMetric('Generation');

    const list: FlowStep[] = [
      {
        id: 'extract',
        label: '추출 (Extract)',
        sublabel: '텍스트/구조화',
        icon: PipelineIcons.Extract,
        durationMs: extract?.averageTimeMs,
        description: '원본 문서에서 텍스트와 구조를 추출하는 단계입니다.',
      },
      {
        id: 'chunking',
        label: '청크 분할 (Chunking)',
        sublabel: '토큰 단위 분리',
        icon: PipelineIcons.Chunking,
        durationMs: chunk?.averageTimeMs,
        description: '문서를 일정 크기의 청크로 분할합니다.',
      },
      {
        id: 'embedding',
        label: '임베딩 (Embedding)',
        sublabel: '벡터 변환',
        icon: PipelineIcons.Embedding,
        durationMs: embed?.averageTimeMs,
        description: '텍스트를 벡터 임베딩으로 변환합니다.',
      },
      {
        id: 'query-embed',
        label: '쿼리 임베딩',
        sublabel: '질문 벡터화',
        icon: PipelineIcons.QueryEmbed,
        durationMs: queryEmbed?.averageTimeMs,
        description: '사용자 쿼리를 임베딩으로 변환합니다.',
      },
      {
        id: 'searching',
        label: '검색 (Search)',
        sublabel: 'Vector / Hybrid',
        icon: PipelineIcons.Searching,
        durationMs: search?.averageTimeMs,
        description: '벡터/하이브리드 검색으로 관련 컨텍스트를 조회합니다.',
      },
      {
        id: 'reranker',
        label: '재정렬 (Cross Encoder)',
        sublabel: '정확도 향상',
        icon: PipelineIcons.Reranker,
        durationMs: crossEncoder?.averageTimeMs,
        description: 'Cross Encoder로 후보 컨텍스트를 재정렬해 최적의 순서를 찾습니다.',
      },
      {
        id: 'generation',
        label: '생성 (LLM)',
        sublabel: '최종 응답',
        icon: PipelineIcons.Generation,
        durationMs: gen?.averageTimeMs,
        description: 'LLM이 최종 답변을 생성하는 단계입니다.',
      },
    ];

    return list;
  }, [metrics]);

  //   const [activeId, setActiveId] = useState<FlowStepId | undefined>(undefined);

  // 전체 파이프라인 총 응답 시간 (단순 합)
  const totalMs = useMemo(
    () => steps.reduce((sum, s) => sum + (typeof s.durationMs === 'number' ? s.durationMs : 0), 0),
    [steps]
  );

  // 샘플 수: 각 단계 count 합산 (5분 동안 처리한 총 단계 샘플)
  const totalSamples = useMemo(() => metrics.reduce((sum, m) => sum + m.count, 0), [metrics]);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">RAG 파이프라인 응답 시간</h3>
          <p className="text-xs text-gray-500">
            최근 5분 평균 · 단계별 처리 시간 · 총 {msLabel(totalMs)}
          </p>
        </div>
        {data && (
          <div className="flex items-center gap-1 text-[11px] text-gray-500">
            <span className="rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-medium text-violet-600">
              5분 평균
            </span>
            <span className="rounded-full bg-gray-50 px-2.5 py-1">샘플 수: {totalSamples}</span>
          </div>
        )}
      </div>

      <div className={clsx('flex-1 min-h-[220px]')}>
        {isLoading ? (
          <div className="flex h-full items-center justify-center text-xs text-gray-400">
            로딩 중…
          </div>
        ) : isError ? (
          <div className="flex h-full items-center justify-center text-xs text-red-500">
            응답 시간 데이터를 불러오지 못했어요.
          </div>
        ) : metrics.length === 0 ? (
          <div className="flex h-full items-center justify-center text-xs text-gray-400">
            아직 수집된 메트릭이 없습니다.
          </div>
        ) : (
          <PipelineFlow steps={steps} />
        )}
      </div>
    </div>
  );
}
