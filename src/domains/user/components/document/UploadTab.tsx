import { useMemo, useState } from 'react';
import FileDropzone from '@/shared/components/file/FileUploader';
import UploadedFileList from '@/shared/components/file/UploadedFileList';
import type { UploadedDoc as UDoc } from '@/shared/components/file/UploadedFileList';
import { uploadFiles } from '@/shared/api/file.api';
import { toast } from 'react-toastify';

type UploadPayload = { files: File[]; category: string; categoryName?: string };

export default function UploadTab() {
  const [uploadedDocs, setUploadedDocs] = useState<UDoc[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);

  const detectType = (f: File): UDoc['type'] => {
    const name = f.name.toLowerCase();
    if (name.endsWith('.pdf')) return 'pdf';
    if (name.endsWith('.md')) return 'md';
    if (name.endsWith('.doc') || name.endsWith('.docx')) return 'docx';
    if (name.endsWith('.xlsx')) return 'xlsx';
    return 'txt';
  };

  const makeDoc = (f: File, category: string, categoryName?: string): UDoc => ({
    id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}_${f.name}`,
    name: f.name,
    sizeKB: f.size / 1024,
    uploadedAt: new Date().toLocaleString(),
    category: categoryName ?? category,
    categoryId: category,
    type: detectType(f),
    file: f,
  });

  // 업로드 → 일단 리스트에 추가 (이름 충돌 처리는 UploadedFileList에서 해결)
  const handleUpload = ({ files, category, categoryName }: UploadPayload) => {
    const mapped = files.map((f) => makeDoc(f, category, categoryName));
    setUploadedDocs((prev) => [...mapped, ...prev]);
  };

  // 서버 업로드(선택 항목)
  const ingestSelected = async () => {
    if (uploading) return;
    setUploading(true);

    const targets = uploadedDocs.filter((d) => selectedIds.includes(d.id) && d.file);
    if (targets.length === 0) {
      setUploading(false);
      return;
    }

    setUploadedDocs((prev) =>
      prev.map((doc) =>
        selectedIds.includes(doc.id) ? ({ ...doc, status: 'pending' } as UDoc) : doc
      )
    );

    let successCount = 0;

    const grouped = targets.reduce<Record<string, UDoc[]>>((acc, doc) => {
      const key = doc.categoryId ?? doc.category ?? '기타';
      (acc[key] ||= []).push(doc);
      return acc;
    }, {});

    for (const [categoryNo, docs] of Object.entries(grouped)) {
      try {
        const files = docs.map((d) => d.file!).filter(Boolean);
        const res = await uploadFiles({ files, categoryNo });

        const isOk = res?.data?.isSuccess === true || res?.status === 201;
        const fileNos: string[] = (res?.data?.result?.data?.fileNos ?? []).map(String);

        if (isOk) successCount += docs.length;

        setUploadedDocs((prev) => {
          const idxById = new Map(docs.map((d, i) => [d.id, i]));
          return prev.map((doc) => {
            const idx = idxById.get(doc.id);
            if (idx === undefined) return doc;
            return { ...doc, status: 'uploaded', fileNo: fileNos[idx] } as UDoc;
          });
        });
      } catch {
        const idSet = new Set(docs.map((d) => d.id));
        setUploadedDocs((prev) =>
          prev.map((doc) => (idSet.has(doc.id) ? ({ ...doc, status: 'failed' } as UDoc) : doc))
        );
      }
    }

    setUploading(false);

    if (successCount > 0) {
      toast.success(`문서 ${successCount}개 업로드 완료!`);
      setTimeout(() => window.location.reload(), 500);
    }
  };

  const handleDownload = (id: string) => {
    const doc = uploadedDocs.find((d) => d.id === id);
    if (!doc?.file) return;
    const url = URL.createObjectURL(doc.file);
    const a = document.createElement('a');
    a.href = url;
    a.download = doc.name; // 리네임된 이름이 파일 저장명에 반영됩니다.
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = (ids: string[]) => {
    setUploadedDocs((prev) => prev.filter((d) => !ids.includes(d.id)));
    setSelectedIds((prev) => prev.filter((id) => !ids.includes(id)));
  };

  // ★ 리네임 반영: UploadedFileList가 충돌 처리 시 호출
  const handleRename = (id: string, nextName: string) => {
    setUploadedDocs((prev) =>
      prev.map((d) => (d.id === id ? ({ ...d, name: nextName } as UDoc) : d))
    );
  };

  const selectedDocs = useMemo(
    () => uploadedDocs.filter((d) => selectedIds.includes(d.id)),
    [uploadedDocs, selectedIds]
  );

  const selectedKB = useMemo(
    () => selectedDocs.reduce((s, d) => s + (d.sizeKB ?? 0), 0),
    [selectedDocs]
  );

  const selectedStr =
    selectedKB >= 1024 ? `${(selectedKB / 1024).toFixed(1)} MB` : `${selectedKB.toFixed(1)} KB`;

  const hasPending = selectedDocs.some((d) => d.status === 'pending');
  const canIngest = selectedIds.length > 0 && !hasPending;

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
        onRename={handleRename}
        brand="retina"
        onSelectChange={setSelectedIds}
      />

      {selectedIds.length > 0 && (
        <div className="mt-6">
          <div className="mx-auto w-full rounded-xl border p-4 bg-white/95 shadow-sm backdrop-blur">
            <div className="flex justify-between items-center gap-3">
              <p className="text-sm text-gray-700">
                선택 {selectedIds.length}개 · {selectedStr}
              </p>
              <button
                type="button"
                onClick={ingestSelected}
                disabled={!canIngest || uploading}
                className="px-4 py-2 text-sm font-semibold rounded text-white bg-[var(--color-retina)] hover:bg-[var(--color-retina)]/90 disabled:opacity-60"
              >
                {uploading ? '문서 업로드 중...' : '문서 업로드'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
