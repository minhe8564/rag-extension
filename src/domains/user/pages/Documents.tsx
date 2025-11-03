import { useState } from 'react';
import FileDropzone from '@/shared/components/FileUploader';
import UploadedFileList from '@/shared/components/UploadedFileList';
import type { UploadedDoc as UDoc } from '@/shared/components/UploadedFileList';

type Category = '업무 매뉴얼' | '정책/규정' | '개발 문서' | '홍보자료' | '이미지' | '기타';

export default function Documents() {
  const [uploadedDocs, setUploadedDocs] = useState<UDoc[]>([]);

  const detectType = (f: File): UDoc['type'] => {
    const t = f.type;
    if (t.includes('pdf')) return 'pdf';
    if (t.includes('presentation') || /\.pptx?$/i.test(f.name)) return 'pptx';
    if (t.includes('sheet') || /\.xlsx?$/i.test(f.name)) return 'xlsx';
    if (t.includes('word') || /\.docx?$/i.test(f.name)) return 'docx';
    if (t.startsWith('image/')) return 'image';
    return 'txt';
  };

  const handleUpload = async (payload: { files: File[]; category: Category }) => {
    const { files, category } = payload;
    const now = new Date().toLocaleString();

    const mapped: UDoc[] = files.map(f => ({
      id: globalThis.crypto?.randomUUID?.() ?? `${Date.now()}_${f.name}`,
      name: f.name,
      sizeKB: f.size / 1024,
      uploadedAt: now,
      category,
      type: detectType(f),
      file: f,
    }));

    setUploadedDocs(prev => [...mapped, ...prev]);
  };

  const handleDownload = (id: string) => {
    const doc = uploadedDocs.find(d => d.id === id);
    if (!doc?.file) return;
    const url = URL.createObjectURL(doc.file);
    const a = document.createElement('a');
    a.href = url;
    a.download = doc.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8 px-4 mb-20">
      <div>
        <h1 className="text-2xl font-semibold mb-2">내 문서</h1>
        <p className="text-sm text-gray-600">
          업로드한 문서를 확인하고 새 문서를 추가할 수 있습니다.
        </p>
      </div>

      <FileDropzone
        onUpload={handleUpload}
        accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
        maxSizeMB={50}
        className="mt-4"
        brand="retina"
        defaultCategory="기타"
      />

      <UploadedFileList
        docs={uploadedDocs}
        onDownload={handleDownload}
        onDelete={ids => setUploadedDocs(prev => prev.filter(d => !ids.includes(d.id)))}
        brand="retina"
      />
    </div>
  );
}
