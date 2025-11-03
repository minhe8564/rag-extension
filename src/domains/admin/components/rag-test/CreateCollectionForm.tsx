import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import Card from '@/shared/components/Card';
import Select from '@/shared/components/Select';
import { ingestTemplateOptions } from '@/domains/admin/components/rag-settings/options';
import FileDropzone from '@/shared/components/FileUploader';
import UploadedFileList from '@/shared/components/UploadedFileList';
import type { UploadedDoc as UDoc } from '@/shared/components/UploadedFileList';
import type { Collection } from '@/domains/admin/components/rag-test/types';

type Props = {
  onCancel: () => void;
  onCreate: (c: Collection) => void;
};
type Category = '업무 매뉴얼' | '정책/규정' | '개발 문서' | '홍보자료' | '이미지' | '기타';

export function CreateCollectionForm({}: Props) {
  const navigate = useNavigate();

  const defaultTemplate = (ingestTemplateOptions as any)?.[0]?.value ?? '';
  const [name, setName] = useState('');
  const [template, setTemplate] = useState<string>(defaultTemplate);
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

  const handleDelete = (ids: string[]) => {
    setUploadedDocs(prev => prev.filter(d => !ids.includes(d.id)));
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Card
          title="Ingest 템플릿 설정"
          tip="Ingest 템플릿을 통해 테스트할 Collection을 생성하세요."
        >
          <div className="flex flex-wrap items-center gap-2">
            <div className="min-w-[220px] w-full sm:w-auto sm:min-w-[260px]">
              <Select
                value={template}
                onChange={setTemplate}
                options={ingestTemplateOptions as any}
                placeholder="선택하세요"
                aria-label="Ingest 템플릿 선택"
              />
            </div>

            <button
              type="button"
              onClick={() => navigate('/admin/rag/settings')}
              className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm font-medium
                         text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Plus className="size-4" />
              <span className="hidden sm:inline">템플릿 추가하기</span>
            </button>
          </div>
        </Card>

        <Card title="Collection 이름 지정" tip="새 컬렉션 이름을 입력해 등록하세요.">
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="예: HEBEES Test"
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-base
                         focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent"
            />
          </div>
        </Card>
      </div>

      <Card title="테스트 문서 업로드">
        <FileDropzone
          onUpload={handleUpload}
          accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg"
          maxSizeMB={50}
          className="mt-4"
          brand="hebees"
        />

        <UploadedFileList
          docs={uploadedDocs}
          onDownload={handleDownload}
          onDelete={handleDelete}
          brand="hebees"
        />
      </Card>
    </div>
  );
}
