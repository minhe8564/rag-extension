import UploadFile from '@/domains/admin/components/documents/UploadFile';
import UploadList from '@/domains/admin/components/documents/UploadList';
import ColSection from '@/domains/admin/components/documents/ColSection';
import SelectVectorization from '@/domains/admin/components/documents/SelectVectorization';
import DuplicatedModal from '@/domains/admin/components/documents/DuplicatedModal';
import type { FileType } from '@/domains/admin/types/documents.types';

import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';

export default function UploadTab() {
  // 업로드된 파일 상태 관리
  const [uploadedFiles, setUploadedFiles] = useState<FileType[]>([]);
  const [duplicates, setDuplicates] = useState<FileType[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 업로드 문서 선택(왼쪽)
  const [selectedFiles, setSelectedFiles] = useState<FileType[]>([]);
  // 컬렉션 선택(오른쪽)
  const [selectedCollection, setSelectedCollection] = useState<'public' | 'hebees' | null>(null);
  // 두 조건이 충족되면 생기는 최종 선택목록
  const [finalSelectedFiles, setFinalSelectedFiles] = useState<FileType[]>([]);

  const handleFilesSelected = (merged: FileType[]) => {
    setUploadedFiles(merged);
  };

  const handleDuplicateDetected = (dups: FileType[]) => {
    setDuplicates(dups);
    setIsModalOpen(true);
  };

  const confirmOverwrite = () => {
    const newNames = new Set(duplicates.map((f) => f.name));
    const filtered = uploadedFiles.filter((f) => !newNames.has(f.name));
    setUploadedFiles([...filtered, ...duplicates]);
    setIsModalOpen(false);
  };

  // 업로드 목록 변경 처리: 업로드 목록 갱신 + 체크 초기화 + 최종 선택 목록 동기화
  const handleFilesChange = (nextFiles: FileType[]) => {
    setUploadedFiles(nextFiles);
    setSelectedFiles([]);
    const existingNames = new Set(nextFiles.map((f) => f.name));
    setFinalSelectedFiles((prev) => prev.filter((f) => existingNames.has(f.name)));
  };

  // 컬렉션 선택 (ColSection에서 온거)
  const handleCollectionSelect = (collectionName: 'public' | 'hebees' | null) => {
    setSelectedCollection(collectionName);
  };

  useEffect(() => {
    if (selectedFiles.length > 0 && selectedCollection) {
      const combined = selectedFiles.map((file) => ({
        ...file,
        collection: selectedCollection,
      }));

      setFinalSelectedFiles((prev) => {
        // 파일명+컬렉션 조합으로만 중복을 방지하여
        // 동일 파일을 다른 컬렉션에 중복 햐추가할 수 있게 함
        const existingComposite = new Set(prev.map((f) => `${f.name}::${f.collection}`));

        // 배치 내부 중복까지 포함해서 한 번에 수집
        const seen = new Set(existingComposite);
        const toAdd: FileType[] = [];
        const blockedNames: string[] = [];

        for (const f of combined) {
          const key = `${f.name}::${f.collection}`;
          if (seen.has(key)) {
            blockedNames.push(f.name);
          } else {
            seen.add(key);
            toAdd.push(f);
          }
        }

        if (blockedNames.length > 0) {
          const uniques = Array.from(new Set(blockedNames));
          const bulletList = uniques.map((n) => `- ${n}`).join('\n');
          toast.warn(
            <div
              style={{ whiteSpace: 'pre-line' }}
            >{`이미 같은 컬렉션에 선택된 문서가 있어요:\n${bulletList}`}</div>
          );
        }
        return [...prev, ...toAdd];
      });

      setSelectedFiles([]);
      setTimeout(() => setSelectedCollection(null), 0); // 다음 렌더 프레임에서 컬렉션 초기화
    }
  }, [selectedFiles, selectedCollection]);

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
          onFilesChange={handleFilesChange}
          onSelectFiles={setSelectedFiles}
          selectedFiles={selectedFiles}
        />
        <ColSection
          selectedCollection={selectedCollection}
          onCollectionSelect={handleCollectionSelect}
        />
      </div>
      <SelectVectorization
        finalSelectedFiles={finalSelectedFiles}
        onRemove={(file) => {
          setFinalSelectedFiles((prev) =>
            prev.filter((f) => !(f.name === file.name && f.collection === file.collection))
          );
          setSelectedFiles([]);
        }}
      />
    </>
  );
}
