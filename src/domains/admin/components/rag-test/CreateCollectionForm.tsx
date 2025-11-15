import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import Card from '@/shared/components/Card';
import Select from '@/shared/components/controls/Select';
import FileDropzone from '@/shared/components/file/FileUploader';
import UploadedFileList from '@/shared/components/file/UploadedFileList';
import type { UploadedDoc as UDoc } from '@/shared/types/file.types';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import type { RagOptions } from '@/domains/admin/components/rag-settings/options';

type Props = {
  onCancel: () => void;
  onCreate: (c: Collection) => void;
  options?: RagOptions | null;
  loadingOptions?: boolean;
  optionsError?: boolean;
};

export function CreateCollectionForm({
  // onCancel,
  // onCreate,
  options,
  loadingOptions,
  optionsError,
}: Props) {
  const navigate = useNavigate();

  const defaultTemplate = useMemo(
    () => options?.ingestTemplate?.[0]?.value ?? '',
    [options?.ingestTemplate]
  );

  const [name, setName] = useState('');
  const [template, setTemplate] = useState<string>(defaultTemplate);
  const [uploadedDocs, setUploadedDocs] = useState<UDoc[]>([]);

  useEffect(() => {
    if (!template && defaultTemplate) setTemplate(defaultTemplate);
  }, [defaultTemplate, template]);

  const detectType = (f: File): UDoc['type'] => {
    const name = f.name.toLowerCase();
    if (name.endsWith('.pdf')) return 'pdf';
    if (name.endsWith('.md')) return 'md';
    if (name.endsWith('.doc') || name.endsWith('.docx')) return 'docx';
    if (name.endsWith('.xlsx')) return 'xlsx';
    return 'txt';
  };

  const handleUpload = ({ files, category }: { files: File[]; category: string }): void => {
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
                options={options?.ingestTemplate ?? []}
                placeholder={loadingOptions ? '불러오는 중…' : '선택하세요'}
                aria-label="Ingest 템플릿 선택"
                disabled={loadingOptions || !!optionsError}
              />
            </div>

            <button
              type="button"
              onClick={() => navigate('/admin/rag/settings')}
              className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Plus className="size-4" />
              <span className="hidden sm:inline">템플릿 추가하기</span>
            </button>
          </div>

          {optionsError && (
            <p className="mt-2 text-sm text-red-500">
              옵션을 불러오지 못했습니다. 설정 화면에서 확인하세요.
            </p>
          )}
        </Card>

        <Card title="Collection 이름 지정" tip="새 컬렉션 이름을 입력해 등록하세요.">
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: HEBEES Test"
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-base focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-transparent"
            />
          </div>
        </Card>
      </div>

      <Card title="테스트 문서 업로드">
        <FileDropzone
          onUpload={handleUpload}
          accept=".pdf,.md,.doc,.docx,.xlsx"
          maxSizeMB={100}
          className="mt-4"
          brand="hebees"
          defaultCategory="기타"
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
