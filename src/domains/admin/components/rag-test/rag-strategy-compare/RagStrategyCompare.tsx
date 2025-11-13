import { useMemo, useState } from 'react';
import { CompareControls } from './CompareControls';
import { CompareResults } from './CompareResults';

export type CompareMode = 'query-2' | 'ingest-2';

export type IngestStrategy = { id: string; name: string; [k: string]: unknown };
export type QueryStrategy = { id: string; name: string; [k: string]: unknown };

export type CompareSide = {
  ingest: IngestStrategy | null | undefined;
  query: QueryStrategy | null | undefined;
};

export type RunCompareArgs = {
  question: string;
  left: CompareSide;
  right: CompareSide;
  mode: CompareMode;
};

export type RunCompareResult = { left: string; right: string };
export type RunCompareFn = (args: RunCompareArgs) => Promise<RunCompareResult> | RunCompareResult;

type Props = {
  initialIngest?: IngestStrategy[];
  initialQueries?: QueryStrategy[];
  onRunCompare?: RunCompareFn;
};

export function RagStrategyCompare({ initialIngest, initialQueries, onRunCompare }: Props) {
  const ingest = initialIngest ?? [
    { id: 'ing-bm25', name: 'BM25 기본' },
    { id: 'ing-dense', name: 'Dense(FAISS)' },
    { id: 'ing-hybrid', name: 'Hybrid(BM25+Dense)' },
  ];
  const queries = initialQueries ?? [
    { id: 'q-basic', name: '기본 프롬프트' },
    { id: 'q-cot', name: 'Chain-of-Thought' },
    { id: 'q-guard', name: '수정/정정 강조' },
  ];

  const [mode, setMode] = useState<CompareMode>('query-2');
  const [question, setQuestion] = useState('');

  const [fixedIngestId, setFixedIngestId] = useState<string | null>(ingest[0]?.id ?? null);
  const [leftQueryId, setLeftQueryId] = useState<string | null>(queries[0]?.id ?? null);
  const [rightQueryId, setRightQueryId] = useState<string | null>(queries[1]?.id ?? null);

  const [fixedQueryId, setFixedQueryId] = useState<string | null>(queries[0]?.id ?? null);
  const [leftIngestId, setLeftIngestId] = useState<string | null>(ingest[0]?.id ?? null);
  const [rightIngestId, setRightIngestId] = useState<string | null>(ingest[1]?.id ?? null);

  const [isRunning, setIsRunning] = useState(false);
  const [leftResult, setLeftResult] = useState<string | null>(null);
  const [rightResult, setRightResult] = useState<string | null>(null);

  const ingestMap = useMemo(() => new Map(ingest.map((i) => [i.id, i] as const)), [ingest]);
  const queryMap = useMemo(() => new Map(queries.map((q) => [q.id, q] as const)), [queries]);

  const buildSides = (): { left: CompareSide; right: CompareSide } => {
    if (mode === 'query-2') {
      const fixedIngest = fixedIngestId ? ingestMap.get(fixedIngestId) : null;
      return {
        left: { ingest: fixedIngest, query: leftQueryId ? queryMap.get(leftQueryId) : null },
        right: { ingest: fixedIngest, query: rightQueryId ? queryMap.get(rightQueryId) : null },
      };
    }
    const fixedQuery = fixedQueryId ? queryMap.get(fixedQueryId) : null;
    return {
      left: { ingest: leftIngestId ? ingestMap.get(leftIngestId) : null, query: fixedQuery },
      right: { ingest: rightIngestId ? ingestMap.get(rightIngestId) : null, query: fixedQuery },
    };
  };

  const run = async () => {
    if (!question.trim()) return;
    setIsRunning(true);
    setLeftResult(null);
    setRightResult(null);

    const { left, right } = buildSides();

    try {
      if (onRunCompare) {
        const res = await onRunCompare({ question, left, right, mode });
        setLeftResult(res.left ?? '');
        setRightResult(res.right ?? '');
      } else {
        // 데모 모드
        await new Promise((r) => setTimeout(r, 300));
        setLeftResult(
          `LEFT\n[${mode}] ${left.ingest?.name ?? '-'} × ${left.query?.name ?? '-'}\nQ: ${question}`
        );
        setRightResult(
          `RIGHT\n[${mode}] ${right.ingest?.name ?? '-'} × ${right.query?.name ?? '-'}\nQ: ${question}`
        );
      }
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <section className="space-y-6">
      <CompareControls
        {...{
          mode,
          setMode,
          question,
          setQuestion,
          initialIngest: ingest,
          initialQueries: queries,
          fixedIngestId,
          leftQueryId,
          rightQueryId,
          fixedQueryId,
          leftIngestId,
          rightIngestId,
          setFixedIngestId,
          setLeftQueryId,
          setRightQueryId,
          setFixedQueryId,
          setLeftIngestId,
          setRightIngestId,
          onRun: run,
          isRunning,
        }}
      />
      <CompareResults leftResult={leftResult} rightResult={rightResult} />
    </section>
  );
}
