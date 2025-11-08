import { useEffect, useRef, useState } from 'react';
import RagPipeline from '@/domains/admin/components/rag-settings/RagPipeline';
import type { TabKey } from '@/domains/admin/components/rag-settings/RagPipeline';
import { IngestSettingsForm } from '@/domains/admin/components/rag-settings/IngestSettingsForm';
import { QuerySettingsForm } from '@/domains/admin/components/rag-settings/QuerySettingsForm';
import { TemplateList } from '@/domains/admin/components/rag-settings/TemplateList';
import SegmentedTabs from '@/shared/components/SegmentedTabs';
import { Settings, UploadCloud, Search } from 'lucide-react';

const TAB_KEY_STORAGE = 'rag.settings.activeTab';

const getInitialTab = (): TabKey => {
  if (typeof window === 'undefined') return 'ingest';
  const q = new URLSearchParams(window.location.search).get('tab');
  if (q === 'ingest' || q === 'query') return q;
  const saved = localStorage.getItem(TAB_KEY_STORAGE);
  return saved === 'ingest' || saved === 'query' ? (saved as TabKey) : 'ingest';
};

export default function RagSettings() {
  const [activeTab, setActiveTab] = useState<TabKey>(getInitialTab());
  const [ingestTemplate, setIngestTemplate] = useState('ingest-1');
  const [queryTemplate, setQueryTemplate] = useState('query-1');

  const anchors = {
    extract: useRef<HTMLDivElement | null>(null),
    chunking: useRef<HTMLDivElement | null>(null),
    embedding: useRef<HTMLDivElement | null>(null),
    'query-embed': useRef<HTMLDivElement | null>(null),
    searching: useRef<HTMLDivElement | null>(null),
    reranker: useRef<HTMLDivElement | null>(null),
    prompting: useRef<HTMLDivElement | null>(null),
    generation: useRef<HTMLDivElement | null>(null),
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TAB_KEY_STORAGE, activeTab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', activeTab);
    window.history.replaceState({}, '', url);
  }, [activeTab]);

  const onSave = async (payload: unknown) => {
    console.log('save settings', payload);
  };

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

      <RagPipeline
        activeTab={activeTab}
        onTabChange={setActiveTab}
        anchors={anchors}
        className="mt-2"
      />

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

      {activeTab === 'ingest' && (
        <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            <div ref={anchors.extract} />
            <div ref={anchors.chunking} />
            <div ref={anchors.embedding} />
            <IngestSettingsForm
              template={ingestTemplate}
              onTemplateChange={setIngestTemplate}
              onSave={onSave}
            />
          </div>
          <aside className="space-y-4">
            <TemplateList kind="ingest" active={ingestTemplate} onSelect={setIngestTemplate} />
          </aside>
        </section>
      )}

      {activeTab === 'query' && (
        <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-6">
            <div ref={anchors['query-embed']} />
            <div ref={anchors.searching} />
            <div ref={anchors.reranker} />
            <div ref={anchors.prompting} />
            <div ref={anchors.generation} />
            <QuerySettingsForm
              template={queryTemplate}
              onTemplateChange={setQueryTemplate}
              onSave={onSave}
            />
          </div>
          <aside className="space-y-4">
            <TemplateList kind="query" active={queryTemplate} onSelect={setQueryTemplate} />
          </aside>
        </section>
      )}
    </div>
  );
}
