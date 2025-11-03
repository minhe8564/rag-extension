import UploadFile from '@/domains/admin/components/documents/UploadFile';
import UploadList from '@/domains/admin/components/documents/UploadList';
import ColSection from '@/domains/admin/components/documents/ColSection';
import SelectVectorization from '@/domains/admin/components/documents/SelectVectorization';
import DuplicatedModal from '@/domains/admin/components/documents/DuplicatedModal';

import { useState } from 'react';

export default function UploadTab() {
  // 업로드된 파일 상태 관리
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [duplicates, setDuplicates] = useState<File[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 컬렉션 선택된 파일 상태 관리
  const [_selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const handleFilesSelected = (merged: File[]) => {
    setUploadedFiles(merged);
  };

  const handleDuplicateDetected = (dups: File[]) => {
    setDuplicates(dups);
    setIsModalOpen(true);
  };

  const confirmOverwrite = () => {
    const newNames = new Set(duplicates.map((f) => f.name));
    const filtered = uploadedFiles.filter((f) => !newNames.has(f.name));
    setUploadedFiles([...filtered, ...duplicates]);
    setIsModalOpen(false);
  };

  return (
    <>
      <UploadFile
        existingFiles={uploadedFiles}
        onFilesSelected={handleFilesSelected}
        onDuplicateDetected={handleDuplicateDetected}
      />
      {isModalOpen && (
        <DuplicatedModal
          duplicates={duplicates}
          onConfirm={confirmOverwrite}
          onCancel={() => setIsModalOpen(false)}
        />
      )}
      <div className="flex gap-4">
        <UploadList
          files={uploadedFiles}
          onFilesChange={setUploadedFiles}
          onSelectFiles={(selectedFiles) => setSelectedFiles(selectedFiles)}
        />
        <ColSection />
      </div>
      <SelectVectorization />
    </>
  );
}
