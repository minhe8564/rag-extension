import type { FileType } from '@/domains/admin/types/documents.types';
import FileUploader from '@/shared/components/file/FileUploader';
interface UploadFileProps {
  onFilesSelected: (mergedFiles: FileType[]) => void; // 최종 병합 결과
  onDuplicateDetected?: (duplicates: FileType[]) => void; // 중복 파일 모달 띄우기 용
  existingFiles: FileType[]; // 부모가 가진 기존 파일 목록
}

export default function UploadFile({
  onFilesSelected,
  onDuplicateDetected,
  existingFiles,
}: UploadFileProps) {
  const handleFiles = ({ files, category }: { files: File[]; category: string }) => {
    if (!files || files.length === 0) return;

    const newFiles: FileType[] = Array.from(files).map((f) => ({
      name: f.name,
      size: f.size,
      category,
      collection: null,
      currentProgress: null,
      currentPercent: null,
      totalProgress: null,
    }));

    const existingNames = new Set(existingFiles.map((f) => f.name));

    // 중복 감지
    const duplicates = newFiles.filter((f) => existingNames.has(f.name));
    const uniqueFiles = newFiles.filter((f) => !existingNames.has(f.name));

    // 중복 있으면 모달 표시
    if (duplicates.length > 0 && onDuplicateDetected) {
      onDuplicateDetected(duplicates);
    }

    // 새 파일은 기존 목록에 추가
    const merged = [...existingFiles, ...uniqueFiles];
    onFilesSelected(merged); // 부모에 전달
  };

  return (
    <section className="space-y-2 my-3">
      <FileUploader onUpload={handleFiles} accept=".pdf,.xlsx" multiple brand="hebees" />
    </section>
  );
}
