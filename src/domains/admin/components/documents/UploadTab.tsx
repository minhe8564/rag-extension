import { useState, useEffect } from 'react';
import FileUploader from '@/shared/components/file/FileUploader';
import UploadList from '@/domains/admin/components/documents/UploadList';
import ColSection from '@/domains/admin/components/documents/ColSection';
import SelectVectorization from '@/domains/admin/components/documents/SelectVectorization';
import type { RawMyDoc } from '@/shared/types/file.types';
import { toast } from 'react-toastify';

function createRawMyDoc(f: File, category: string): RawMyDoc {
  const INITIAL_STATUS: RawMyDoc['status'] = 'PENDING';

  return {
    fileNo: crypto.randomUUID(),
    name: f.name,
    size: f.size,
    type: f.type,
    bucket: '',
    path: '',
    categoryNo: category,
    collectionNo: '',
    createdAt: new Date().toISOString(),
    originalFile: f,
    status: INITIAL_STATUS,
  };
}

export default function UploadTab() {
  const [uploadedFiles, setUploadedFiles] = useState<RawMyDoc[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<RawMyDoc[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [finalSelectedFiles, setFinalSelectedFiles] = useState<RawMyDoc[]>([]);

  const handleUpload = ({ files, category }: { files: File[]; category: string }) => {
    if (!files || files.length === 0) return;
    const newFiles = Array.from(files).map((f) => createRawMyDoc(f, category));
    setUploadedFiles((prev) => [...prev, ...newFiles]);
  };

  const handleCollectionSelect = (name: string | null) => {
    setSelectedCollection(name);
  };

  useEffect(() => {
    if (selectedFiles.length > 0 && selectedCollection) {
      const combined = selectedFiles.map((f) => ({
        ...f,
        collectionNo: selectedCollection,
      }));

      setFinalSelectedFiles((prev) => {
        const existingKeys = new Set(prev.map((f) => `${f.fileNo}::${f.collectionNo}`));
        const newOnes = combined.filter(
          (f) => !existingKeys.has(`${f.fileNo}::${selectedCollection}`)
        );
        if (newOnes.length === 0) {
          toast('⚠️ 해당 파일은 이미 선택 목록에 존재합니다.');
          return prev;
        }
        return [...prev, ...newOnes];
      });

      setSelectedFiles([]);
      setSelectedCollection(null);
    }
  }, [selectedFiles, selectedCollection]);

  const handleRemoveFromFinal = (file: RawMyDoc) => {
    setFinalSelectedFiles((prev) =>
      prev.filter((f) => !(f.fileNo === file.fileNo && f.collectionNo === file.collectionNo))
    );
  };

  return (
    <section className="flex flex-col gap-4 my-4">
      <FileUploader onUpload={handleUpload} accept=".pdf,.xlsx" multiple brand="hebees" />

      <div className="flex gap-4">
        <div className="flex-[2]">
          <UploadList
            files={uploadedFiles}
            selectedFiles={selectedFiles}
            onFilesChange={setUploadedFiles}
            onSelectFiles={setSelectedFiles}
          />
        </div>

        <div className="flex-[2]">
          <ColSection
            selectedCollection={selectedCollection}
            onCollectionSelect={handleCollectionSelect}
            uploadedFiles={finalSelectedFiles}
          />
        </div>
      </div>

      <SelectVectorization
        finalSelectedFiles={finalSelectedFiles}
        onRemove={handleRemoveFromFinal}
      />
    </section>
  );
}
