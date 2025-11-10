import Tooltip from '@/shared/components/Tooltip';
import { AlertTriangle } from 'lucide-react';

type Props = {
  conflictCount: number;
  onOverwriteAll: () => void;
  onRenameAll: () => void;
  hidden?: boolean;
};

export default function ConflictBar({ conflictCount, onOverwriteAll, onRenameAll, hidden }: Props) {
  if (hidden || conflictCount <= 0) return null;

  const warnBg = 'bg-amber-50';
  const warnBorder = 'border-amber-300';
  const warnText = 'text-amber-700';

  return (
    <div
      className={`mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3 ${warnBorder} ${warnBg}`}
    >
      <div className="flex items-center gap-2 text-sm">
        <AlertTriangle className={warnText} size={16} />
        <span className="text-gray-700">
          파일명 중복이 <b>{conflictCount}</b>건 발견되었어요. 처리 방법을 선택하세요.
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Tooltip content="각 그룹에서 최신 1개만 남기고 삭제" side="bottom" offset={2}>
          <button
            onClick={onOverwriteAll}
            className="rounded-md border px-3 py-1.5 text-sm hover:bg-white"
          >
            최신만 남기기
          </button>
        </Tooltip>
        <Tooltip content="중복 항목에 (2), (3) 자동 붙이기" side="bottom" offset={2}>
          <button
            onClick={onRenameAll}
            className="rounded-md border px-3 py-1.5 text-sm hover:bg-white"
          >
            전부 자동 리네임
          </button>
        </Tooltip>
      </div>
    </div>
  );
}
