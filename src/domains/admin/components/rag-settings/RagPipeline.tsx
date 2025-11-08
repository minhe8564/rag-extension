import { useMemo, useState } from 'react';
import PipelineFlow from '@/shared/components/rag/PipelineFlow';
import type { FlowStep, FlowStepId } from '@/shared/components/rag/PipelineFlow';
import { PipelineIcons } from '@/shared/components/rag/PipelineIcons';
import { Zap } from 'lucide-react';

export type TabKey = 'ingest' | 'query';

export type RagPipelineProps = {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
  anchors: Partial<Record<FlowStepId, React.RefObject<HTMLDivElement>>>;
  className?: string;
};

const stepTabMap: Record<FlowStepId, TabKey> = {
  extract: 'ingest',
  chunking: 'ingest',
  embedding: 'ingest',
  'query-embed': 'query',
  searching: 'query',
  reranker: 'query',
  prompting: 'query',
  generation: 'query',
};

export default function RagPipeline({ activeTab, onTabChange, anchors }: RagPipelineProps) {
  const [activeFlowStep, setActiveFlowStep] = useState<FlowStepId>('extract');

  const steps: FlowStep[] = useMemo(
    () => [
      {
        id: 'extract',
        label: 'Extract',
        sublabel: '문서 수집',
        icon: PipelineIcons.Extract,
        description: '문서를 불러오고\n분석 가능한 형태로 준비합니다.',
      },
      {
        id: 'chunking',
        label: 'Chunking',
        sublabel: '문서 분할',
        icon: PipelineIcons.Chunking,
        description: '긴 문서를 의미 단위로 나누어\n처리 효율을 높입니다.',
      },
      {
        id: 'embedding',
        label: 'Embedding',
        sublabel: '벡터화',
        icon: PipelineIcons.Embedding,
        description: '분할된 문서를\n벡터 형태로 변환합니다.',
      },
      {
        id: 'query-embed',
        label: 'Query Embed',
        sublabel: '쿼리 벡터화',
        icon: PipelineIcons.QueryEmbed,
        description: '사용자의 질문을 벡터로 변환해\n검색 기준을 만듭니다.',
      },
      {
        id: 'searching',
        label: 'Searching',
        sublabel: '검색',
        icon: PipelineIcons.Searching,
        description: '가장 연관성 높은 문서를\n벡터 DB에서 탐색합니다.',
      },
      {
        id: 'reranker',
        label: 'Re-ranker',
        sublabel: '재정렬',
        icon: PipelineIcons.Reranker,
        description: '검색 결과를 의미 기반으로\n재정렬해 정확도를 높입니다.',
      },
      {
        id: 'prompting',
        label: 'Prompting',
        sublabel: '프롬프트',
        icon: PipelineIcons.Prompting,
        description: '최종 답변 생성을 위한\n프롬프트를 구성합니다.',
      },
      {
        id: 'generation',
        label: 'Generation',
        sublabel: '응답 생성',
        icon: PipelineIcons.Generation,
        description: 'LLM이 문맥 기반으로\n최종 답변을 생성합니다.',
      },
    ],
    []
  );

  const handleStepClick = (id: FlowStepId) => {
    setActiveFlowStep(id);
    const targetTab = stepTabMap[id];
    if (activeTab !== targetTab) onTabChange(targetTab);

    requestAnimationFrame(() => {
      setTimeout(
        () => anchors[id]?.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }),
        0
      );
    });
  };

  return (
    <div className="rounded-2xl border bg-white p-8 shadow-sm">
      <div className="mb-10">
        <div className="flex items-center justify-between">
          <div className="text-gray-800">
            <div className="flex items-start gap-3">
              <Zap size={18} className="text-[var(--color-hebees)] mt-1" />
              <h3 className="text-xl font-semibold text-gray-900">RAG 파이프라인</h3>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              AI가 질문을 이해하고 정보를 탐색해 답변을 생성하는 과정입니다.
            </p>
          </div>
        </div>
      </div>

      <PipelineFlow
        steps={steps}
        activeId={activeFlowStep}
        onStepClick={handleStepClick}
        className="mb-4"
      />
    </div>
  );
}
