export type FileType = {
  name: string;
  size: number | null;
  category: string | null;
  collection: 'public' | 'hebees' | null;
  currentProgress: string | null;
  currentPercent: number | null;
  totalProgress: number | null;
};

export interface ColSectionProps {
  selectedCollection: 'public' | 'hebees' | null;
  onCollectionSelect: (collectionName: 'public' | 'hebees' | null) => void;
}

export interface UploadedDocumentsProps {
  files: FileType[];
  onFilesChange?: (updatedFiles: FileType[]) => void; // 부모에 반영하고 싶을 때 사용
  onSelectFiles: (selectedFiles: FileType[]) => void; // 컬렉션 선택으로 넘길 파일을 부모로 전달
  selectedFiles: FileType[];
}
