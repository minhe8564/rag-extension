import { useEffect, useMemo, useRef, useState } from 'react';
import RagPipeline, { type TabKey } from '@/domains/admin/components/rag-settings/RagPipeline';
import SegmentedTabs from '@/shared/components/SegmentedTabs';
import { Settings, UploadCloud, Search } from 'lucide-react';

import { getStrategies } from '@/domains/admin/api/rag-settings/strategies.api';
import { makeRagOptions } from '@/domains/admin/components/rag-settings/options';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';

import ConfirmModal from '@/shared/components/ConfirmModal';

import IngestTab from '@/domains/admin/components/rag-settings/ingest/IngestTab';
import QueryTab from '@/domains/admin/components/rag-settings/query/QueryTab';

import { deleteIngestTemplate } from '@/domains/admin/api/rag-settings/ingest-templates.api';
import { deleteQueryTemplate } from '@/domains/admin/api/rag-settings/query-templates.api';

const TAB_KEY_STORAGE = 'rag.settings.activeTab';
const getInitialTab = (): TabKey => {
  if (typeof window === 'undefined') return 'ingest';
  const q = new URLSearchParams(window.location.search).get('tab');
  if (q === 'ingest' || q === 'query') return q as TabKey;
  const saved = localStorage.getItem(TAB_KEY_STORAGE);
  return saved === 'ingest' || saved === 'query' ? (saved as TabKey) : 'ingest';
};

export default function RagSettings() {
  const [activeTab, setActiveTab] = useState<TabKey>(getInitialTab());

  const [ragOptions, setRagOptions] = useState<RagOptions | null>(null);
  const [optionsLoading, setOptionsLoading] = useState(false);

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<{
    kind: 'ingest' | 'query';
    id: string;
  } | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TAB_KEY_STORAGE, activeTab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', activeTab);
    window.history.replaceState({}, '', url);
  }, [activeTab]);

  useEffect(() => {
    const run = async () => {
      try {
        setOptionsLoading(true);
        const strategies = await getStrategies();
        const map = makeRagOptions(strategies);
        setRagOptions(map);
      } finally {
        setOptionsLoading(false);
      }
    };
    void run();
  }, []);

  const requestDeleteIngest = (id: string) => {
    setConfirmTarget({ kind: 'ingest', id });
    setConfirmOpen(true);
  };
  const requestDeleteQuery = (id: string) => {
    setConfirmTarget({ kind: 'query', id });
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!confirmTarget) return;
    try {
      if (confirmTarget.kind === 'ingest') {
        await deleteIngestTemplate(confirmTarget.id);
      } else {
        await deleteQueryTemplate(confirmTarget.id);
      }
      window.location.reload();
    } finally {
      setConfirmOpen(false);
      setConfirmTarget(null);
    }
  };

  const onCreate = () => window.location.reload();

  const extractRef = useRef<HTMLDivElement | null>(null);
  const chunkingRef = useRef<HTMLDivElement | null>(null);
  const embeddingRef = useRef<HTMLDivElement | null>(null);
  const queryEmbedRef = useRef<HTMLDivElement | null>(null);
  const searchingRef = useRef<HTMLDivElement | null>(null);
  const rerankerRef = useRef<HTMLDivElement | null>(null);
  const promptingRef = useRef<HTMLDivElement | null>(null);
  const generationRef = useRef<HTMLDivElement | null>(null);

  const anchors = useMemo(
    () => ({
      extract: extractRef,
      chunking: chunkingRef,
      embedding: embeddingRef,
      'query-embed': queryEmbedRef,
      searching: searchingRef,
      reranker: rerankerRef,
      prompting: promptingRef,
      generation: generationRef,
    }),
    []
  );

  const pipeline = useMemo(
    () => (
      <RagPipeline
        activeTab={activeTab}
        onTabChange={setActiveTab}
        anchors={anchors}
        className="mt-2"
      />
    ),
    [activeTab, anchors]
  );

  return (
    <div className="space-y-8 px-4 mb-20">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-gradient-to-r from-[#EED8F3]/70 to-[#CBE1FF]/70 flex items-center justify-center">
          <Settings size={28} className="text-[var(--color-hebees)]" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">
            <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
              HEBEES RAG
            </span>{' '}
            <span className="font-semibold text-black">모델 설정</span>
          </h1>
          <p className="text-sm text-gray-600">
            RAG 모델 파라미터를 설정하고 최적화할 수 있습니다.
          </p>
        </div>
      </div>

      {pipeline}

      <SegmentedTabs
        value={activeTab}
        onChange={(k) => setActiveTab(k as TabKey)}
        tabs={[
          { key: 'ingest', label: 'Ingest 설정', icon: <UploadCloud size={16} /> },
          { key: 'query', label: 'Query 설정', icon: <Search size={16} /> },
        ]}
        className="mt-2"
        brand="hebees"
      />

      {activeTab === 'ingest' ? (
        <IngestTab
          anchors={anchors}
          ragOptions={ragOptions}
          optionsLoading={optionsLoading}
          onRequestDelete={requestDeleteIngest}
          onCreate={onCreate}
        />
      ) : (
        <QueryTab
          anchors={anchors}
          ragOptions={ragOptions}
          optionsLoading={optionsLoading}
          onRequestDelete={requestDeleteQuery}
          onCreate={onCreate}
        />
      )}

      <ConfirmModal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="템플릿 삭제"
        message={`정말로 이 템플릿을 삭제할까요?\n삭제 후에는 복구할 수 없습니다.`}
        confirmText="삭제"
        cancelText="취소"
        variant="danger"
      />
    </div>
  );
}
