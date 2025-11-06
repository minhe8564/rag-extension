import { useMemo, useState } from 'react';
import FileDropzone from '@/shared/components/file/FileUploader';
import UploadedFileList from '@/shared/components/file/UploadedFileList';
import type { UploadedDoc as UDoc } from '@/shared/components/file/UploadedFileList';
import { uploadFiles } from '@/shared/api/file.api';

type UploadPayload = { files: File[]; category: string; categoryName?: string };

export default function UploadTab() {
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

  const handleUpload = ({ files, category, categoryName }: UploadPayload) => {
    const now = new Date().toLocaleString();
    const mapped: UDoc[] = files.map((f) => ({
      id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}_${f.name}`,
      name: f.name,
      sizeKB: f.size / 1024,
      uploadedAt: now,
      category: categoryName ?? category,
      categoryId: category,
      type: detectType(f),
      file: f,
    }));
    setUploadedDocs((prev) => [...mapped, ...prev]);
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
    const targets = selectedDocs.filter((d) => d.file);
    if (targets.length === 0) {
      console.log('선택된 업로드 대상이 없습니다.');
      return;
    }

    setUploadedDocs((prev) =>
      prev.map((doc) => (selectedIds.includes(doc.id) ? { ...doc, status: 'pending' } : doc))
    );

    const byCategory = targets.reduce<Record<string, UDoc[]>>((acc, doc) => {
      const key = doc.categoryId ?? doc.category;
      if (!key) return acc;
      if (!acc[key]) acc[key] = [];
      acc[key]!.push(doc);
      return acc;
    }, {});

    for (const [categoryNo, docs] of Object.entries(byCategory)) {
      try {
        const files = docs.map((d) => d.file!).filter(Boolean);
        const { data } = await uploadFiles({ files, categoryNo });
        const fileNos = data.data.fileNos ?? [];

        setUploadedDocs((prev) => {
          const indexById = new Map(docs.map((d, i) => [d.id, i]));
          return prev.map((doc) => {
            const idx = indexById.get(doc.id);
            if (idx === undefined) return doc;
            return { ...doc, status: 'uploaded', fileNo: fileNos[idx] };
          });
        });
      } catch (err) {
        console.error('uploadFiles error (category:', categoryNo, ')', err);
        setUploadedDocs((prev) => {
          const idSet = new Set(docs.map((d) => d.id));
          return prev.map((doc) => (idSet.has(doc.id) ? { ...doc, status: 'failed' } : doc));
        });
      }
    }
  };

  return (
    <>
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
    </>
  );
}
