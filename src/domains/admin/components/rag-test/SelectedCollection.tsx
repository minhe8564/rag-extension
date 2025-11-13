import { useState } from 'react';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import CollectionDocuments from '@/domains/admin/components/rag-test/CollectionDocuments';

type Props = {
  collection: Collection;
  query?: string;
  setQuery?: (v: string) => void;
  run?: () => Promise<void> | void;
  answer?: string | null;
};

export function SelectedCollection({ collection }: Props) {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="space-y-6">
      <CollectionDocuments
        key={refreshKey}
        collection={collection}
        docs={[
          {
            id: '1',
            name: '히비스_안내문서.pdf',
            sizeKB: 162.6,
            createdAt: '2025.10.21 01:27',
            categoryNo: '업무 매뉴얼',
            type: 'pdf',
          },
          {
            id: '2',
            name: '프로세스_가이드.pdf',
            sizeKB: 98.2,
            createdAt: '2025.10.21 01:27',
            categoryNo: '업무 매뉴얼',
            type: 'pdf',
          },
        ]}
        onUpload={(files) => console.log('upload', files)}
        onDownload={(id) => console.log('download', id)}
        onReindex={(id) => console.log('reindex', id)}
        onDelete={(ids) => console.log('delete', ids)}
        onRefresh={() => setRefreshKey((k) => k + 1)}
      />
    </div>
  );
}
