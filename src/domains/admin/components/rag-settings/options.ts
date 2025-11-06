import type { Option } from '@/shared/components/Select';

export const ingestTemplateOptions: Option[] = [
  { label: 'Ingest 템플릿 1', value: 'ingest-1' },
  { label: 'Ingest 템플릿 2', value: 'ingest-2' },
  { label: 'Ingest 템플릿 3', value: 'ingest-3' },
] as const;

export const queryTemplateOptions: Option[] = [
  { label: 'Query 템플릿 1', value: 'query-1' },
  { label: 'Query 템플릿 2', value: 'query-2' },
  { label: 'Query 템플릿 3', value: 'query-3' },
] as const;

export const extractOptions: Option[] = [
  {
    label: 'pdfPlumber',
    value: 'pdfplumber',
    desc: 'PDF 내부의 텍스트와 표 데이터를 구조적으로 추출',
  },
  { label: 'Marker', value: 'marker', desc: '페이지 내 문단/구역 단위로 마크업 기반 추출' },
  { label: 'paddleOCR', value: 'paddleocr', desc: '이미지에서 한글/영문 텍스트를 OCR로 인식' },
] as const;

export const chunkStrategyOptions: Option[] = [
  { label: '고정 길이', value: 'naive', desc: '일정 길이 기준으로 텍스트를 분할' },
  { label: '의미 기반', value: 'paragraph', desc: 'Markdown 구조를 기준으로 의미 단위 분리' },
  { label: '문단 기반', value: 'heading', desc: '문단 구분을 이용한 자연스러운 분리' },
] as const;

export const embedOptions: Option[] = [
  {
    label: 'multilingual-e5-large',
    value: 'multilingual-e5-large',
    desc: '다국어 문장을 같은 의미 공간에 임베딩',
  },
  { label: 'bge', value: 'bge', desc: '높은 의미 정밀도의 고성능 임베딩' },
] as const;

export const queryTransFormOptions: Option[] = [
  { label: 'HyDE', value: 'hyde', desc: '질문을 가상 답변으로 변환 후 검색 (내부 LLM)' },
  { label: '버퍼', value: 'buffer', desc: 'f(x)=x 형태의 단순 버퍼 함수' },
] as const;

export const searchAlgorithmOptions: Option[] = [
  { label: 'Semantic Search', value: 'semantic', desc: '임베딩 벡터 간 유사도 기반 검색' },
  { label: 'Hybrid Search', value: 'hybrid', desc: '키워드 + 임베딩 벡터 결합 검색' },
] as const;

export const rerankingOptions: Option[] = [
  { label: 'pointwise', value: 'pointwise', desc: '개별 결과의 관련도를 평가하는 방식' },
  { label: 'pairwise', value: 'pairwise', desc: '결과 간 상대적 순위를 비교하는 방식' },
] as const;

export const llmModelsOptions: Option[] = [
  { label: 'GPT-4o', value: 'gpt-4o', desc: '최신 GPT-4o 모델' },
  { label: 'Gemini', value: 'gemini', desc: '구글의 통합형 멀티모달 언어모델' },
  { label: 'Llama', value: 'llama', desc: '메타가 공개한 오픈소스 대형 언어모델' },
  { label: 'GPT-OSS', value: 'gpt-oss', desc: '오픈소스 기반 경량 언어모델' },
  { label: 'Qwen3', value: 'qwen3', desc: '알리바바의 다국어·멀티모달 언어모델' },
] as const;

export const fileTypeOptions: Option[] = [
  { label: '전체', value: 'all' },
  { label: 'PDF', value: 'pdf' },
  { label: 'Word', value: 'docx' },
  { label: 'PPT', value: 'pptx' },
  { label: 'Excel', value: 'xlsx' },
  { label: 'TXT', value: 'txt' },
  { label: 'Image', value: 'image' },
];
