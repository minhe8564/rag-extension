import { useState } from 'react';
import UploadTab from '@/domains/admin/components/documents/UploadTab';
import CollectionTab from '@/domains/admin/components/documents/CollectionTab';

export default function Documents() {
  const [activeTab, setActiveTab] = useState<'upload' | 'collection'>('upload');

  return (
    <main>
      {/* 상단 헤더 + 탭 */}
      <section className="flex items-center gap-4 mb-6">
        <h1 className="text-3xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text text-transparent">
          HEBEES RAG
        </h1>

        <div className="flex items-center gap-6">
          <button
            onClick={() => setActiveTab('upload')}
            className={`text-2xl font-semibold transition-all ${
              activeTab === 'upload'
                ? 'text-black border-b-2 border-[var(--color-hebees)]'
                : 'text-gray-400 hover:text-[var(--color-hebees)]'
            }`}
          >
            문서 업로드
          </button>

          <button
            onClick={() => setActiveTab('collection')}
            className={`text-2xl font-semibold transition-all ${
              activeTab === 'collection'
                ? 'text-black border-b-2 border-[var(--color-hebees)]'
                : 'text-gray-400 hover:text-[var(--color-hebees)]'
            }`}
          >
            컬렉션 관리
          </button>
        </div>
      </section>

      {/* 탭 내용 */}
      <div className="transition-opacity duration-300">
        {activeTab === 'upload' ? <UploadTab /> : <CollectionTab />}
      </div>
    </main>
  );
}
