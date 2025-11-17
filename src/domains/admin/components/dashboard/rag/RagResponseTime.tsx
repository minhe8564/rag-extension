import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import { Zap } from 'lucide-react';

import PipelineFlow, {
  type FlowStep,
  type FlowStepId,
} from '@/shared/components/rag-pipeline/PipelineFlow';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';

import { getRagPipelineResponseTime } from '@/domains/admin/api/system.dashboard.api';
import type {
  RagPipelineResponseTimeMetric,
  RagPipelineResponseTimeResult,
} from '@/domains/admin/types/system.dashboard.types';

const toSec = (ms?: number): number | undefined => {
  if (typeof ms !== 'number') return undefined;

  const sec = ms / 1000;
  const truncated = parseFloat(sec.toFixed(2));

  return truncated;
};

const secLabel = (sec?: number): string => {
  if (typeof sec === 'number' && !Number.isNaN(sec)) {
    const formatted = sec.toFixed(2);
    return `${formatted} s`;
  }

  return '-';
};

const normalizeKey = (s: string) => s.toLowerCase().replace(/\s+/g, '').replace(/-/g, '');

export default function RagResponseTime() {
  const { data, isLoading, isError } = useQuery<RagPipelineResponseTimeResult>({
    queryKey: ['admin', 'dashboard', 'rag', 'pipelineResponseTime'],
    queryFn: getRagPipelineResponseTime,
    staleTime: 30_000,
  });

  const metrics: RagPipelineResponseTimeMetric[] = useMemo(() => data?.metrics ?? [], [data]);

  const steps: FlowStep[] = useMemo(() => {
    const findMetric = (key: string) =>
      metrics.find((m) => normalizeKey(m.name) === normalizeKey(key));

    const extract = findMetric('Extract');
    const chunk = findMetric('Chunking');
    const embed = findMetric('Embedding');
    const queryEmbed = findMetric('Query Embedding');
    const search = findMetric('Search');
    const crossEncoder = findMetric('Cross Encoder');
    const gen = findMetric('Generation');

    return [
      {
        id: 'extract',
        label: 'Extract',
        sublabel: '문서 수집',
        icon: PipelineIcons.Extract,
        description: '문서를 불러오고\n분석 가능한 형태로 준비합니다.',
        durationSec: toSec(extract?.averageTimeMs),
      },
      {
        id: 'chunking',
        label: 'Chunking',
        sublabel: '문서 분할',
        icon: PipelineIcons.Chunking,
        description: '긴 문서를 의미 단위로 나누어\n처리 효율을 높입니다.',
        durationSec: toSec(chunk?.averageTimeMs),
      },
      {
        id: 'embedding',
        label: 'Embedding',
        sublabel: '벡터화',
        icon: PipelineIcons.Embedding,
        description: '분할된 문서를\n벡터 형태로 변환합니다.',
        durationSec: toSec(embed?.averageTimeMs),
      },
      {
        id: 'query-embed',
        label: 'Query Embed',
        sublabel: '쿼리 벡터화',
        icon: PipelineIcons.QueryEmbed,
        description: '사용자의 질문을 벡터로 변환해\n검색 기준을 만듭니다.',
        durationSec: toSec(queryEmbed?.averageTimeMs),
      },
      {
        id: 'searching',
        label: 'Searching',
        sublabel: '검색',
        icon: PipelineIcons.Searching,
        description: '가장 연관성 높은 문서를\n벡터 DB에서 탐색합니다.',
        durationSec: toSec(search?.averageTimeMs),
      },
      {
        id: 'reranker',
        label: 'Re-ranker',
        sublabel: '재정렬',
        icon: PipelineIcons.Reranker,
        description: '검색 결과를 의미 기반으로\n재정렬해 정확도를 높입니다.',
        durationSec: toSec(crossEncoder?.averageTimeMs),
      },
      {
        id: 'generation',
        label: 'Generation',
        sublabel: '응답 생성',
        icon: PipelineIcons.Generation,
        description: 'LLM이 문맥 기반으로\n최종 답변을 생성합니다.',
        durationSec: toSec(gen?.averageTimeMs),
      },
    ];
  }, [metrics]);

  const [activeId, setActiveId] = useState<FlowStepId | undefined>(undefined);

  useEffect(() => {
    if (isLoading || isError || steps.length === 0 || metrics.length === 0) return;

    let index = 0;
    setActiveId(steps[0].id);

    const timer = setInterval(() => {
      index = (index + 1) % steps.length;
      setActiveId(steps[index].id);
    }, 1500);

    return () => clearInterval(timer);
  }, [isLoading, isError, steps, metrics]);

  const totalSec = useMemo(
    () => steps.reduce((sum, step) => sum + (step.durationSec ?? 0), 0),
    [steps]
  );

  const totalSamples = useMemo(() => metrics.reduce((sum, m) => sum + m.count, 0), [metrics]);

  const hasData = useMemo(() => totalSamples > 0 && totalSec > 0, [totalSamples, totalSec]);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="mb-10 flex items-center justify-between gap-2">
        <div>
          <div className="flex items-start gap-3">
            <Zap size={18} className="mt-1 text-[var(--color-hebees)]" />
            <h3 className="text-xl font-semibold text-gray-900">RAG 파이프라인 응답 시간</h3>
          </div>
          <p className="mt-0.5 text-sm text-gray-500">
            최근 5분 평균 · 단계별 처리 시간 ·{' '}
            {hasData ? `총 ${secLabel(totalSec)}` : '아직 집계된 RAG 요청이 없습니다.'}
          </p>
        </div>
        {data && (
          <div className="flex flex-col items-end gap-2 text-sm text-gray-500">
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-[var(--color-hebees-bg)] px-3 py-1 font-medium text-[var(--color-hebees)]">
                5분 평균
              </span>
              <span className="rounded-full bg-gray-50 px-3 py-1">샘플 수: {totalSamples}</span>
            </div>

            {!hasData && (
              <div className="rounded-full bg-amber-50 px-3 py-[6px] text-sm text-amber-700">
                아직 생성된 채팅방/질문이 없어 0s로 집계됩니다
              </div>
            )}
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
          <PipelineFlow steps={steps} activeId={activeId} />
        )}
      </div>
    </div>
  );
}
