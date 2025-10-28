import { Trash2 } from 'lucide-react';
export default function UploadedDocuments() {
  return (
    <section className="flex flex-col w-1/2 p-4 border border-gray-200 rounded-xl">
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text text-transparent w-fit"
      >
        업로드 된 문서
      </h3>

      <div className="flex items-center justify-end gap-3 mb-3 text-sm text-gray-600">
        <label className="flex items-center gap-1 cursor-pointer">
          <p>모두 선택</p>
          <input
            type="checkbox"
            className="
    accent-[var(--color-hebees)]
    border-2 border-[var(--color-hebees)]
    rounded-sm cursor-pointer scale-125
  "
          />
        </label>
        <label className="flex items-center gap-1 cursor-pointer">
          <p>모두 삭제</p>
          <button className="text-[var(--color-hebees)] transition">
            <Trash2 className="w-5 h-5" />
          </button>
        </label>
      </div>

      <div className="flex flex-col items-center justify-center flex-1 text-gray-400 text-sm">
        업로드된 문서가 없습니다.
      </div>
    </section>
  );
}
