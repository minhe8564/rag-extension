import { useEffect, useState } from 'react';
import { FileText, List as ListIcon, Upload as UploadIcon } from 'lucide-react';
import SegmentedTabs from '@/shared/components/controls/SegmentedTabs';
import UploadTab from '@/domains/admin/components/documents/UploadTab';
import CollectionTab from '@/domains/admin/components/documents/CollectionTab';

type TabKey = 'upload' | 'collection';
const TAB_KEY_STORAGE = 'documents.activeTab';

const getInitialTab = (): TabKey => {
  const q = new URLSearchParams(window.location.search).get('tab');
  if (q === 'upload' || q === 'collection') return q;
  const saved = localStorage.getItem(TAB_KEY_STORAGE);
  return saved === 'upload' || saved === 'collection' ? saved : 'collection';
};

export default function Documents() {
  const [activeTab, setActiveTab] = useState<TabKey>(getInitialTab());

  useEffect(() => {
    localStorage.setItem(TAB_KEY_STORAGE, activeTab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', activeTab);
    window.history.replaceState({}, '', url);
  }, [activeTab]);

  return (
    <div className="space-y-8 px-4 mb-20">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-[var(--color-hebees-bg)] flex items-center justify-center">
          <FileText size={26} className="text-[var(--color-hebees)]" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold mb-1">문서 관리</h1>
          <p className="text-sm text-gray-600">업로드하거나, 내 문서 목록을 확인하세요.</p>
        </div>
      </div>

      <SegmentedTabs
        value={activeTab}
        onChange={(k) => setActiveTab(k as TabKey)}
        tabs={[
          { key: 'upload', label: '문서 업로드', icon: <UploadIcon size={16} /> },
          { key: 'collection', label: '컬렉션 관리', icon: <ListIcon size={16} /> },
        ]}
        className="mt-2"
        brand="hebees"
      />

      <div className="mt-4">{activeTab === 'upload' ? <UploadTab /> : <CollectionTab />}</div>
    </div>
  );
}
