import { CloudUpload } from 'lucide-react';

export default function UploadFile() {
  return (
    <section className="space-y-2 my-3">
      <div className="flex flex-col items-center justify-center w-full rounded-xl border border-gray-200 py-10 bg-white">
        <div className="flex items-center justify-center w-14 h-14 rounded-full bg-[var(--color-hebees-bg)] mb-3">
          <CloudUpload size={30} className="text-[var(--color-hebees)]" />
        </div>
        <p className="text-m font-medium text-gray-800 mb-1">파일 업로드</p>
        <p className="text-xs text-gray-400">PDF, 엑셀파일(xlsx) 업로드가 가능합니다.</p>
      </div>
    </section>
  );
}
