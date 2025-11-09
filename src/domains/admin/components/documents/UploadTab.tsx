import { useState, useEffect } from 'react';
import FileUploader from '@/shared/components/file/FileUploader';
import UploadList from '@/domains/admin/components/documents/UploadList';
import ColSection from '@/domains/admin/components/documents/ColSection';
import SelectVectorization from '@/domains/admin/components/documents/SelectVectorization';
import type { RawMyDoc } from '@/shared/types/file.types';
import { toast } from 'react-toastify';

export default function UploadTab() {
  //  업로드된 전체 파일
  const [uploadedFiles, setUploadedFiles] = useState<RawMyDoc[]>([]);

  //  UploadList에서 선택된 파일들
  const [selectedFiles, setSelectedFiles] = useState<RawMyDoc[]>([]);

  //  선택된 컬렉션 (public / hebees)
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  //  컬렉션 지정까지 완료된 최종 선택 목록
  const [finalSelectedFiles, setFinalSelectedFiles] = useState<RawMyDoc[]>([]);

  //  FileUploader → RawMyDoc 변환
  const handleUpload = ({ files, category }: { files: File[]; category: string }) => {
    if (!files || files.length === 0) return;

    const newFiles: RawMyDoc[] = Array.from(files).map((f) => ({
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
    }));

    setUploadedFiles((prev) => [...prev, ...newFiles]);
  };

  // 파일 삭제
  // const handleDelete = (remainingFiles: RawMyDoc[]) => {
  //   setUploadedFiles(remainingFiles);
  //   setSelectedFiles([]);
  // };

  // 컬렉션 선택 시
  const handleCollectionSelect = (name: string | null) => {
    setSelectedCollection(name);
  };

  // 파일 선택 + 컬렉션 선택 시 → SelectVectorization으로 이동
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
        console.log('새로 추가되는 파일들:', newOnes);
        if (newOnes.length === 0) {
          toast('⚠️ 해당 파일은 이미 선택 목록에 존재합니다.');
          return prev; // 중복이면 추가하지 않음
        }
        return [...prev, ...newOnes];
      });

      // 초기화
      setSelectedFiles([]);
      setSelectedCollection(null);
    }
  }, [selectedFiles, selectedCollection]);

  // 선택 목록에서 제거
  const handleRemoveFromFinal = (file: RawMyDoc) => {
    setFinalSelectedFiles((prev) =>
      prev.filter((f) => !(f.fileNo === file.fileNo && f.collectionNo === file.collectionNo))
    );
  };

  return (
    <section className="flex flex-col gap-4 my-4">
      {/* 파일 업로더 */}
      <FileUploader onUpload={handleUpload} accept=".pdf,.xlsx" multiple brand="hebees" />

      {/* 2️업로드된 파일 목록 + 컬렉션 선택 */}
      <div className="flex gap-4">
        {/* 왼쪽: 업로드된 문서 */}
        <div className="flex-[2]">
          <UploadList
            files={uploadedFiles}
            selectedFiles={selectedFiles}
            onFilesChange={setUploadedFiles}
            onSelectFiles={setSelectedFiles}
          />
        </div>

        {/* 오른쪽: 컬렉션 선택 */}
        <div className="flex-[2]">
          <ColSection
            selectedCollection={selectedCollection}
            onCollectionSelect={handleCollectionSelect}
            uploadedFiles={finalSelectedFiles} // 이미 컬렉션이 지정된 파일만 표시
          />
        </div>
      </div>

      {/* 선택 목록 (벡터화 대상) */}
      <SelectVectorization
        finalSelectedFiles={finalSelectedFiles}
        onRemove={handleRemoveFromFinal}
      />
    </section>
  );
}
