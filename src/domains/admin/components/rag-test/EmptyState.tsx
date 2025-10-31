import { FolderPlus } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="rounded-xl border shadow-sm bg-white px-20 py-40 text-center text-gray-500">
      <div className="mx-auto mb-3 grid h-16 w-16 place-items-center rounded-2xl border bg-gray-50">
        <FolderPlus size={28} className="text-gray-600" />
      </div>
      <div className="mb-1 text-base font-medium text-gray-700">컬렉션이 선택되지 않았습니다.</div>
      <div className="text-sm text-gray-400">
        상단에서 기존 컬렉션을 선택하거나 새로 생성해 시작하세요.
      </div>
    </div>
  );
}
