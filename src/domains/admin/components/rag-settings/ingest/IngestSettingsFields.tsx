import { LabelRow } from '@/domains/admin/components/rag-settings/ui/labelRow';
import { Slider } from '@/domains/admin/components/rag-settings/ui/Slider';
import { PipelineIcons } from '@/shared/components/rag-pipeline/PipelineIcons';
import SectionHeader from '@/domains/admin/components/rag-settings/ui/SectionHeader';
import Select from '@/shared/components/Select';
import type { IngestSettingsFieldsProps } from '@/domains/admin/types/rag-settings/ingest/ingestSettings.types';

export default function IngestSettingsFields({
  anchors,
  loading,
  scrollTo,

  extractEngine,
  chunkStrategy,
  chunkSize,
  overlap,
  embedModel,
  embedSparse,

  setExtractEngine,
  setChunkStrategy,
  setChunkSize,
  setOverlap,
  setEmbedModel,
  setEmbedSparse,

  extractOpts,
  chunkOpts,
  embedDenseOpts,
  embedSparseOpts,
}: IngestSettingsFieldsProps) {
  return (
    <>
      <div ref={anchors?.extract} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="extract"
          title="Extract · 문서 수집"
          subtitle="문서에서 텍스트·이미지·표를 추출하는 방법을 선택합니다."
          icon={PipelineIcons.Extract}
          onClick={scrollTo}
        />
        <div className="flex items-center justify-between gap-4">
          <LabelRow label="추출 엔진 선택" hint="PDF/이미지 등 입력 형식에 맞는 엔진을 고르세요." />
          <div className="max-w-xs w-full">
            <Select
              value={extractEngine}
              onChange={setExtractEngine}
              options={extractOpts}
              disabled={loading || extractOpts.length === 0}
            />
          </div>
        </div>
      </div>

      <div ref={anchors?.chunking} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="chunking"
          title="Chunking · 문서 분할"
          subtitle="문서를 의미 단위로 나누어 처리 효율을 높입니다."
          icon={PipelineIcons.Chunking}
          onClick={scrollTo}
        />
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow label="청킹 전략 선택" hint="문서를 나누는 기준을 선택합니다." />
          <div className="max-w-xs w-full">
            <Select
              value={chunkStrategy}
              onChange={setChunkStrategy}
              options={chunkOpts}
              disabled={loading || chunkOpts.length === 0}
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="청크 크기"
            hint="큰 청크는 더 많은 컨텍스트를, 작은 청크는 더 높은 정밀도를 제공합니다."
          />
          <div className="max-w-sm w-full">
            <Slider value={chunkSize} min={1} max={512} onChange={setChunkSize} />
          </div>
        </div>
        <div className="flex items-center justify-between gap-4">
          <LabelRow
            label="오버랩 토큰 수"
            hint="오버랩이 클수록 문맥 연속성은 좋아지지만 중복이 증가합니다."
          />
          <div className="max-w-sm w-full">
            <Slider value={overlap} min={0} max={200} step={1} onChange={setOverlap} />
          </div>
        </div>
      </div>

      <div ref={anchors?.embedding} className="rounded-2xl border bg-white p-8 shadow-sm">
        <SectionHeader
          id="embedding"
          title="Embedding · 벡터화"
          subtitle="분할된 문서를 벡터로 변환합니다. Dense/Sparse를 함께 구성할 수 있어요."
          icon={PipelineIcons.Embedding}
          onClick={scrollTo}
        />
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="임베딩 모델 (Dense)"
            hint="텍스트를 벡터로 변환할 기본 임베딩 모델입니다."
          />
          <div className="max-w-sm w-full">
            <Select
              value={embedModel}
              onChange={setEmbedModel}
              options={embedDenseOpts}
              disabled={loading || embedDenseOpts.length === 0}
            />
          </div>
        </div>
        <div className="mb-6 flex items-center justify-between gap-4">
          <LabelRow
            label="임베딩 모델 (Sparse)"
            hint="희소 벡터 기반 임베딩(예: SPLADE). 하이브리드 검색에 유리합니다."
          />
          <div className="max-w-sm w-full">
            <Select
              value={embedSparse}
              onChange={setEmbedSparse}
              options={embedSparseOpts}
              disabled={loading || embedSparseOpts.length === 0}
            />
          </div>
        </div>
      </div>
    </>
  );
}
