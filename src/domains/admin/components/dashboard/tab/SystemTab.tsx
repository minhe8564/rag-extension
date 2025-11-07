import { useEffect, useState } from 'react';
import Overview from '@/domains/admin/components/dashboard/system/Overview';
import Servers from '@/domains/admin/components/dashboard/system/Servers';
import Storage from '@/domains/admin/components/dashboard/system/Storage';

export default function SystemTab() {
  const [now, setNow] = useState(() => new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date().toLocaleTimeString());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="mt-4 space-y-6">
      <div className="flex justify-end">
        <p className="text-sm text-gray-500">
          시스템 리소스 및 인프라 모니터링 · Last updated: {now}
        </p>
      </div>

      <Overview />

      <Servers />

      <Storage />
    </div>
  );
}
