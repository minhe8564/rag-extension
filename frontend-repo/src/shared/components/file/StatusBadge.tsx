import { Loader2, Check, XCircle, Clock } from 'lucide-react';
import type { RagStatus } from '@/shared/types/file.types';

const normalizeStatus = (s?: string): RagStatus | undefined => {
  if (!s) return undefined;
  const up = s.toUpperCase();
  if (up === 'UPLOADED' || up === 'COMPLETED') return 'COMPLETED';
  if (up === 'PENDING') return 'PENDING';
  if (up === 'INGESTING' || up === 'PROCESSING') return 'INGESTING';
  if (up === 'FAILED') return 'FAILED';
  return undefined;
};

const statusBadge: Record<RagStatus, { label: string; icon: JSX.Element; className: string }> = {
  PENDING: {
    label: '대기중',
    icon: <Clock size={14} className="text-gray-500" />,
    className: 'bg-gray-100 text-gray-600 border border-gray-200',
  },
  INGESTING: {
    label: '처리중',
    icon: <Loader2 size={14} className="animate-spin text-amber-600" />,
    className: 'bg-amber-50 text-amber-700 border border-amber-200',
  },
  COMPLETED: {
    label: '완료',
    icon: <Check size={14} className="text-green-600" />,
    className: 'bg-green-50 text-green-700 border border-green-200',
  },
  FAILED: {
    label: '실패',
    icon: <XCircle size={14} className="text-red-600" />,
    className: 'bg-red-50 text-red-700 border border-red-200',
  },
};

export default function StatusBadge({ status }: { status?: string }) {
  const st = normalizeStatus(status);
  if (!st) return <span className="text-gray-300">-</span>;
  const { label, icon, className } = statusBadge[st];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${className}`}
    >
      {icon}
      {label}
    </span>
  );
}
