import PageHeader from '@/domains/admin/components/dashboard/PageHeader';
import { useState, useEffect } from 'react';
import { Activity, Gauge } from 'lucide-react';
import SegmentedTabs from '@/shared/components/SegmentedTabs';
import RagTab from '@/domains/admin/components/dashboard/tab/RagTab';
import SystemTab from '@/domains/admin/components/dashboard/tab/SystemTab';

type TabKey = 'realtime' | 'ops';
const TAB_KEY_STORAGE = 'rag.dashboard.activeTab';

const getInitialTab = (): TabKey => {
  const q = new URLSearchParams(window.location.search).get('tab');
  if (q === 'realtime' || q === 'ops') return q;
  const saved = localStorage.getItem(TAB_KEY_STORAGE);
  return saved === 'realtime' || saved === 'ops' ? (saved as TabKey) : 'realtime';
};

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabKey>(getInitialTab());

  useEffect(() => {
    localStorage.setItem(TAB_KEY_STORAGE, activeTab);
    const url = new URL(window.location.href);
    url.searchParams.set('tab', activeTab);
    window.history.replaceState({}, '', url);
  }, [activeTab]);

  return (
    <>
      <div className="space-y-8 px-4 mb-20">
        <PageHeader />

        <SegmentedTabs
          value={activeTab}
          onChange={(k) => setActiveTab(k as TabKey)}
          tabs={[
            { key: 'realtime', label: 'RAG 시스템 실시간 모니터링', icon: <Activity size={16} /> },
            { key: 'ops', label: '운영 효율성 대시보드', icon: <Gauge size={16} /> },
          ]}
          className="mt-2"
          brand="retina"
        />

        {activeTab === 'realtime' ? <RagTab /> : <SystemTab />}
      </div>
    </>
  );
}
