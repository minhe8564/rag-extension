import { CircleAlert } from 'lucide-react';
import type { FileType } from '@/domains/admin/types';

interface DuplicatedModalProps {
  duplicates: FileType[];
  onConfirm: () => void;
  onCancel: () => void;
}

export default function DuplicatedModal({ duplicates, onConfirm, onCancel }: DuplicatedModalProps) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
      <h2>
        <CircleAlert size={20} />새 버전의 파일이 업로드 되었습니다.
      </h2>
      <p>업로드 된 파일을 확인하세요.</p>
      <ul>
        {duplicates.map((file) => (
          <li key={file.name}>{file.name}</li>
        ))}
      </ul>
      <button onClick={onConfirm}>덮어쓰기</button>
      <button onClick={onCancel}>취소</button>
    </div>
  );
}
