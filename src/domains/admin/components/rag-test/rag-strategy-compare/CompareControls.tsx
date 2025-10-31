import { ChevronDown, Loader2, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

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
  const nav = useNavigate();

  const Select = (p: React.SelectHTMLAttributes<HTMLSelectElement>) => (
    <div className="relative">
      <select
        {...p}
        className={
          'w-full appearance-none rounded-md border bg-white px-3 py-2 pr-8 text-sm ' +
          (p.className ?? '')
        }
      />
      <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-4 w-4 opacity-60" />
    </div>
  );

  return (
    <div className="rounded-xl border bg-white p-4 space-y-3">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Query 템플릿 / Ingest 전략 비교</h2>
        <button
          type="button"
          onClick={() => nav('/admin/rag/settings')}
          className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1.5 text-sm hover:bg-gray-50"
        >
          <Plus className="h-4 w-4" />새 템플릿 추가하기
        </button>
      </div>

      {/* 모드 전환 */}
      <div className="inline-flex rounded-lg border bg-gray-50 p-1 text-sm">
        <button
          onClick={() => props.setMode('query-2')}
          className={
            'rounded-md px-3 py-1.5 ' +
            (props.mode === 'query-2' ? 'bg-white shadow' : 'text-gray-600')
          }
        >
          Query 2개 비교
        </button>
        <button
          onClick={() => props.setMode('ingest-2')}
          className={
            'rounded-md px-3 py-1.5 ' +
            (props.mode === 'ingest-2' ? 'bg-white shadow' : 'text-gray-600')
          }
        >
          Ingest 2개 비교
        </button>
      </div>

      {/* 질문 */}
      <textarea
        placeholder="질문을 입력하세요."
        value={props.question}
        onChange={e => props.setQuestion(e.target.value)}
        className="h-24 w-full resize-none rounded-md border bg-gray-50 p-3 text-sm"
      />

      {/* 셀렉터 */}
      {props.mode === 'query-2' ? (
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <p className="mb-1 text-xs text-gray-600">Ingest (공통)</p>
            <Select
              value={props.fixedIngestId ?? ''}
              onChange={e => props.setFixedIngestId(e.target.value || null)}
            >
              <option value="">선택</option>
              {props.initialIngest.map(i => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <p className="mb-1 text-xs text-gray-600">Left Query</p>
            <Select
              value={props.leftQueryId ?? ''}
              onChange={e => props.setLeftQueryId(e.target.value || null)}
            >
              <option value="">선택</option>
              {props.initialQueries.map(q => (
                <option key={q.id} value={q.id}>
                  {q.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <p className="mb-1 text-xs text-gray-600">Right Query</p>
            <Select
              value={props.rightQueryId ?? ''}
              onChange={e => props.setRightQueryId(e.target.value || null)}
            >
              <option value="">선택</option>
              {props.initialQueries.map(q => (
                <option key={q.id} value={q.id}>
                  {q.name}
                </option>
              ))}
            </Select>
          </div>
        </div>
      ) : (
        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <p className="mb-1 text-xs text-gray-600">Query (공통)</p>
            <Select
              value={props.fixedQueryId ?? ''}
              onChange={e => props.setFixedQueryId(e.target.value || null)}
            >
              <option value="">선택</option>
              {props.initialQueries.map(q => (
                <option key={q.id} value={q.id}>
                  {q.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <p className="mb-1 text-xs text-gray-600">Left Ingest</p>
            <Select
              value={props.leftIngestId ?? ''}
              onChange={e => props.setLeftIngestId(e.target.value || null)}
            >
              <option value="">선택</option>
              {props.initialIngest.map(i => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <p className="mb-1 text-xs text-gray-600">Right Ingest</p>
            <Select
              value={props.rightIngestId ?? ''}
              onChange={e => props.setRightIngestId(e.target.value || null)}
            >
              <option value="">선택</option>
              {props.initialIngest.map(i => (
                <option key={i.id} value={i.id}>
                  {i.name}
                </option>
              ))}
            </Select>
          </div>
        </div>
      )}

      {/* 실행 버튼 */}
      <button
        type="button"
        onClick={props.onRun}
        disabled={props.isRunning}
        className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-black px-4 py-2 text-sm text-white"
      >
        {props.isRunning && <Loader2 className="h-4 w-4 animate-spin" />}
        템플릿/전략 비교 실행
      </button>
    </div>
  );
}
