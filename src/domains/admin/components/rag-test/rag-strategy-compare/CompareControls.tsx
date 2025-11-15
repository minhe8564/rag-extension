import Card from '@/shared/components/Card';
import Select from '@/shared/components/controls/Select';
import { Loader2, BarChart3 } from 'lucide-react';

type Props = {
  mode: 'query-2' | 'ingest-2';
  setMode: (m: 'query-2' | 'ingest-2') => void;
  question: string;
  setQuestion: (v: string) => void;

  // selectors
  initialIngest: { id: string; name: string }[];
  initialQueries: { id: string; name: string }[];

  fixedIngestId: string | null;
  leftQueryId: string | null;
  rightQueryId: string | null;
  fixedQueryId: string | null;
  leftIngestId: string | null;
  rightIngestId: string | null;

  setFixedIngestId: (v: string | null) => void;
  setLeftQueryId: (v: string | null) => void;
  setRightQueryId: (v: string | null) => void;
  setFixedQueryId: (v: string | null) => void;
  setLeftIngestId: (v: string | null) => void;
  setRightIngestId: (v: string | null) => void;

  onRun: () => void;
  isRunning: boolean;
};

export function CompareControls(props: Props) {
  // {id,name} -> {label,value}
  const ingestOptions = props.initialIngest.map((o) => ({ label: o.name, value: o.id }));
  const queryOptions = props.initialQueries.map((o) => ({ label: o.name, value: o.id }));

  return (
    <>
      <Card
        title="HEBEES RAG 파이프라인 비교"
        subtitle="벡터화된 Collection을 기반으로, Query 전략을 적용해 성능을 비교합니다."
      >
        <div className="relative inline-flex rounded-md bg-gray-100 p-1 text-sm mb-3">
          <span
            className={`absolute h-[32px] w-[120px] rounded-md bg-white shadow transition-all duration-300 ease-out ${
              props.mode === 'ingest-2' ? 'translate-x-0' : 'translate-x-[120px]'
            }`}
          />
          <button
            onClick={() => props.setMode('ingest-2')}
            className={`relative z-10 w-[120px] px-3 py-1.5 text-center font-medium transition-colors ${
              props.mode === 'ingest-2' ? 'text-gray-900' : 'text-gray-500'
            }`}
          >
            Ingest 비교
          </button>

          <button
            onClick={() => props.setMode('query-2')}
            className={`relative z-10 w-[120px] px-3 py-1.5 text-center font-medium transition-colors ${
              props.mode === 'query-2' ? 'text-gray-900' : 'text-gray-500'
            }`}
          >
            Query 비교
          </button>
        </div>

        {props.mode === 'query-2' ? (
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-md border bg-white p-3 shadow-sm">
              <p className="mb-2 text-xs font-medium text-gray-500">
                Ingest
                <span className="ml-2 rounded-sm border px-1 py-0.5 text-[11px] text-gray-600">
                  공통
                </span>
              </p>
              <Select
                value={props.fixedIngestId ?? ''}
                onChange={(v: string) => props.setFixedIngestId(v || null)}
                options={ingestOptions}
              />
            </div>

            <div className="rounded-md border bg-white p-3 shadow-sm">
              <p className="mb-2 text-xs font-medium text-gray-500">
                <span className="bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text font-semibold text-transparent">
                  Query
                </span>
                <span className="ml-2 rounded-sm bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700">
                  왼쪽
                </span>
              </p>
              <Select
                value={props.leftQueryId ?? ''}
                onChange={(v: string) => props.setLeftQueryId(v || null)}
                options={queryOptions}
              />
            </div>

            <div className="rounded-md border bg-white p-3 shadow-sm">
              <p className="mb-2 text-xs font-medium text-gray-500">
                <span className="bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text font-semibold text-transparent">
                  Query
                </span>
                <span className="ml-2 rounded-sm bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700">
                  오른쪽
                </span>
              </p>
              <Select
                value={props.rightQueryId ?? ''}
                onChange={(v: string) => props.setRightQueryId(v || null)}
                options={queryOptions}
              />
            </div>
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-md border bg-white p-3 shadow-sm">
              <p className="mb-2 text-xs font-medium text-gray-500">
                Query
                <span className="ml-2 rounded-sm border px-1 py-0.5 text-[10px] text-gray-600">
                  공통
                </span>
              </p>
              <Select
                value={props.fixedQueryId ?? ''}
                onChange={(v: string) => props.setFixedQueryId(v || null)}
                options={queryOptions}
              />
            </div>

            <div className="rounded-md border bg-white p-3 shadow-sm">
              <p className="mb-2 text-xs font-medium text-gray-500">
                <span className="bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text font-semibold text-transparent">
                  Ingest
                </span>
                <span className="ml-2 rounded-sm bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700">
                  왼쪽
                </span>
              </p>
              <Select
                value={props.leftIngestId ?? ''}
                onChange={(v: string) => props.setLeftIngestId(v || null)}
                options={ingestOptions}
              />
            </div>

            <div className="rounded-md border bg-white p-3 shadow-sm">
              <p className="mb-2 text-xs font-medium text-gray-500">
                <span className="bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text font-semibold text-transparent">
                  Ingest
                </span>
                <span className="ml-2 rounded-sm bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700">
                  오른쪽
                </span>
              </p>
              <Select
                value={props.rightIngestId ?? ''}
                onChange={(v: string) => props.setRightIngestId(v || null)}
                options={ingestOptions}
              />
            </div>
          </div>
        )}

        <textarea
          placeholder="질문을 입력하세요."
          value={props.question}
          onChange={(e) => {
            const v = e.target.value;
            if (v.length <= 300) props.setQuestion(v);
          }}
          className="
            mt-6 h-28 w-full resize-none rounded-md bg-gray-100 p-4 text-sm
            outline-none focus:outline-none border-none focus:border-none
            ring-0 focus:ring-0 focus:ring-transparent
            transition
          "
        />
        <div className="mt-1 flex justify-end text-xs text-gray-400">
          {props.question.length}/300
        </div>

        <button
          type="button"
          onClick={props.onRun}
          disabled={props.isRunning}
          className="
            mt-6 w-full inline-flex items-center justify-center gap-2
            rounded-md px-4 py-3 text-base font-medium
            transition-all active:scale-[0.98]
            text-black
            bg-[linear-gradient(90deg,rgba(190,125,177,0.10),rgba(129,186,255,0.20))]
            hover:bg-[linear-gradient(90deg,rgba(190,125,177,0.18),rgba(129,186,255,0.28))]
            disabled:opacity-50 disabled:cursor-not-allowed
          "
        >
          {props.isRunning ? (
            <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
          ) : (
            <BarChart3 className="h-4 w-4 text-gray-600" />
          )}
          <span className="font-semibold">
            {props.isRunning ? '실행 중...' : '템플릿 / 전략 비교 실행'}
          </span>
        </button>
      </Card>
    </>
  );
}
