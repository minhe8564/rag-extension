import { useMemo, useState } from 'react';
import FileDropzone from '@/shared/components/file/FileUploader';
import UploadedFileList from '@/shared/components/file/UploadedFileList';
import type { UploadedDoc as UDoc } from '@/shared/components/file/UploadedFileList';
import { FileText } from 'lucide-react';

export default function Documents() {
  const [uploadedDocs, setUploadedDocs] = useState<UDoc[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const detectType = (f: File): UDoc['type'] => {
    const name = f.name.toLowerCase();
    if (name.endsWith('.pdf')) return 'pdf';
    if (name.endsWith('.md')) return 'md';
    if (name.endsWith('.doc') || name.endsWith('.docx')) return 'docx';
    if (name.endsWith('.xlsx')) return 'xlsx';
    return 'txt';
  };

  const handleUpload = ({ files, category }: { files: File[]; category: string }) => {
    const now = new Date().toLocaleString();

    const mapped: UDoc[] = files.map((f) => ({
      id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}_${f.name}`,
      name: f.name,
      sizeKB: f.size / 1024,
      uploadedAt: now,
      category,
      type: detectType(f),
      file: f,
    }));

    setUploadedDocs((prev) => [...mapped, ...prev]);

    // 서버 업로드 필요 시 여기서 FormData 비동기 호출 (void 유지)
  };

  const handleDownload = (id: string) => {
    const doc = uploadedDocs.find((d) => d.id === id);
    if (!doc?.file) return;
    const url = URL.createObjectURL(doc.file);
    const a = document.createElement('a');
    a.href = url;
    a.download = doc.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = (ids: string[]) => {
    setUploadedDocs((prev) => prev.filter((d) => !ids.includes(d.id)));
    setSelectedIds((prev) => prev.filter((id) => !ids.includes(id)));
  };

  const selectedDocs = useMemo(
    () => uploadedDocs.filter((d) => selectedIds.includes(d.id)),
    [uploadedDocs, selectedIds]
  );

  const selectedTotalKB = useMemo(
    () => selectedDocs.reduce((sum, d) => sum + (d.sizeKB ?? 0), 0),
    [selectedDocs]
  );

  const selectedTotalStr =
    selectedTotalKB >= 1024
      ? `${(selectedTotalKB / 1024).toFixed(1)} MB`
      : `${selectedTotalKB.toFixed(1)} KB`;

  const ingestSelected = async () => {
    // const payload = selectedDocs.map(d => ({ id: d.id }));  // 또는 파일/카테고리 등
    // await fastApi.post('/api/v1/rag/ingest', payload);
    console.log(
      'INGEST start:',
      selectedDocs.map((d) => d.name)
    );
  };

  return (
    <div className="space-y-8 px-4 mb-20">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-[var(--color-retina-bg)] flex items-center justify-center">
          <FileText size={26} className="text-[var(--color-retina)]" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold mb-1">내 문서</h1>
          <p className="text-sm text-gray-600">
            업로드한 문서를 확인하고 새 문서를 추가할 수 있습니다.
          </p>
        </div>
      </div>

      <FileDropzone
        onUpload={handleUpload}
        accept=".pdf,.md,.doc,.docx,.xlsx"
        maxSizeMB={100}
        className="mt-4"
        brand="retina"
        defaultCategory="기타"
      />

      <UploadedFileList
        docs={uploadedDocs}
        onDownload={handleDownload}
        onDelete={handleDelete}
        brand="retina"
        onSelectChange={setSelectedIds}
      />

      {selectedIds.length > 0 && (
        <div className="mt-6">
          <div className="mx-auto w-full rounded-xl border border-gray-200 bg-white/95 backdrop-blur p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-gray-700">
                선택된 파일 <span className="font-medium">{selectedIds.length}</span>개 · 총{' '}
                <span className="font-medium">{selectedTotalStr}</span>
              </p>

              <button
                type="button"
                onClick={ingestSelected}
                className="inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-semibold text-white bg-[var(--color-retina)] hover:bg-[var(--color-retina)]/90"
              >
                문서 업로드
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
