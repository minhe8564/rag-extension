import { ArrowDown, ArrowUp } from 'lucide-react';

export function NetworkMetrics({
  inboundMbps,
  outboundMbps,
  bandwidthMbps,
}: {
  inboundMbps: number;
  outboundMbps: number;
  bandwidthMbps?: number;
  usagePercent?: number;
}) {
  return (
    <div className="flex flex-col gap-4 py-4 rounded-xl bg-white mt-6 border-gray-100">
      <div className="flex justify-between px-10 items-end">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-1">
            <ArrowUp size={22} className="text-orange-500" />
            <span className="text-sm text-gray-500 font-medium">OUT</span>
          </div>
          <span className="text-2xl font-semibold text-gray-900 tabular-nums leading-none">
            {outboundMbps.toFixed(1)}
            <span className="ml-1 text-sm text-gray-500 font-normal">Mbps</span>
          </span>
        </div>

        <div className="flex flex-col items-end gap-1.5">
          <div className="flex items-center gap-1">
            <span className="text-sm text-gray-500 font-medium">IN</span>
            <ArrowDown size={22} className="text-blue-500" />
          </div>
          <span className="text-2xl font-semibold text-gray-900 tabular-nums leading-none">
            {inboundMbps.toFixed(1)}
            <span className="ml-1 text-sm text-gray-500 font-normal">Mbps</span>
          </span>
        </div>
      </div>

      <div className="flex justify-end text-xs text-gray-500 pt-4 border-gray-100">
        <span>대역폭 {bandwidthMbps ? `${bandwidthMbps} Mbps` : '-'}</span>
      </div>
    </div>
  );
}
