import type {
  Strategy,
  StrategyParameter,
} from '@/domains/admin/types/rag-settings/strategies.types';
import type { Option } from '@/shared/components/controls/Select';

// 파일 타입 옵션
export const fileTypeOptions: Option[] = [
  { label: '전체', value: 'all' },
  { label: 'PDF', value: 'pdf' },
  { label: 'Markdown', value: 'md' },
  { label: 'Word', value: 'docx' },
  { label: 'Excel', value: 'xlsx' },
];

// 옵션 구조
export type RagOptions = {
  ingestTemplate: Option[];
  queryTemplate: Option[];

  extract: Option[];
  chunk: Option[];
  embedDense: Option[];
  embedSparse: Option[];
  transform: Option[];
  searchSemantic: Option[];
  searchHybrid: Option[];
  rerank: Option[];
  promptUser: Option[];
  promptSystem: Option[];
  generation: Option[];
};

// Strategy → Option
const toOption = (s: Strategy): Option => ({
  label: s.name,
  value: s.strategyNo,
  desc: s.description,
});

// retrieval subtype 타입가드
function isRetrievalParam(param: StrategyParameter): param is { type: 'semantic' | 'hybrid' } {
  return (
    (typeof param === 'object' &&
      param !== null &&
      'type' in param &&
      (param as Record<string, unknown>).type === 'semantic') ||
    (param as Record<string, unknown>).type === 'hybrid'
  );
}

// subtype 추출
function getRetrievalSubtype(param: StrategyParameter | undefined): 'semantic' | 'hybrid' | null {
  if (!param) return null;
  return isRetrievalParam(param) ? param.type : null;
}

// 전략 리스트 → 옵션맵
export function makeRagOptions(strategies: Strategy[]): RagOptions {
  const opts: RagOptions = {
    ingestTemplate: [],
    queryTemplate: [],

    extract: [],
    chunk: [],
    embedDense: [],
    embedSparse: [],
    transform: [],
    searchSemantic: [],
    searchHybrid: [],
    rerank: [],
    promptUser: [],
    promptSystem: [],
    generation: [],
  };

  strategies.forEach((s) => {
    const item = toOption(s);
    const param = s.parameter;

    switch (s.type) {
      case 'extraction':
        opts.extract.push(item);
        break;

      case 'chunking':
        opts.chunk.push(item);
        break;

      case 'embedding-dense':
        opts.embedDense.push(item);
        break;

      case 'embedding-sparse':
        opts.embedSparse.push(item);
        break;

      case 'transformation':
        opts.transform.push(item);
        break;

      case 'retrieval': {
        const subtype = getRetrievalSubtype(param);
        if (subtype === 'hybrid') opts.searchHybrid.push(item);
        else opts.searchSemantic.push(item);
        break;
      }

      case 'reranking':
        opts.rerank.push(item);
        break;

      case 'prompting-user':
        opts.promptUser.push(item);
        break;

      case 'prompting-system':
        opts.promptSystem.push(item);
        break;

      case 'generation':
        opts.generation.push(item);
        break;
    }
  });

  return opts;
}
