import { useState } from 'react';
import { IngestSettingsForm } from '@/domains/admin/components/rag-settings/IngestSettingsForm';
import { QuerySettingsForm } from '@/domains/admin/components/rag-settings/QuerySettingsForm';
import { TemplateList } from '@/domains/admin/components/rag-settings/TemplateList';

export default function RagSettings() {
  const [ingestTemplate, setIngestTemplate] = useState('ingest-1');
  const [queryTemplate, setQueryTemplate] = useState('query-1');

  const onSave = async (payload: any) => {
    console.log('save settings', payload);
    // await apiInstance.post('/rag/settings', payload)
  };

  return (
    <div className="space-y-8 px-4 mb-20">
      <h1 className="text-2xl">
        <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
          HEBEES RAG
        </span>{' '}
        <span className="font-semibold text-black">모델 설정</span>
      </h1>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <IngestSettingsForm
            template={ingestTemplate}
            onTemplateChange={setIngestTemplate}
            onSave={onSave}
          />
        </div>
        <aside className="space-y-4">
          <TemplateList
            kind="ingest"
            active={ingestTemplate}
            onSelect={v => setIngestTemplate(v)}
            onEdit={v => console.log('[ingest] edit', v)}
            onDelete={v => console.log('[ingest] delete', v)}
          />
        </aside>
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <QuerySettingsForm
            template={queryTemplate}
            onTemplateChange={setQueryTemplate}
            onSave={onSave}
          />
        </div>
        <aside className="space-y-4">
          <TemplateList
            kind="query"
            active={queryTemplate}
            onSelect={v => setQueryTemplate(v)}
            onEdit={v => console.log('[query] edit', v)}
            onDelete={v => console.log('[query] delete', v)}
          />
        </aside>
      </section>
    </div>
  );
}
