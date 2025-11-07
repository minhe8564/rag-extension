import { ArrowDown, ArrowUp } from 'lucide-react';
import type { ReactNode } from 'react';

export function Network({
  inbound,
  outbound,
  bandwidth,
  topRight,
}: {
  inbound: number;
  outbound: number;
  bandwidth: number;
  topRight?: ReactNode; // StatusPill 등
}) {
  return (
    <>
      {/* 상단: 오른쪽에 상태 뱃지/시간 */}
      <div className="flex items-start justify-between">
        <div />
        {topRight}
      </div>

      {/* 중앙: IN / OUT 두 칸 */}
      <div className="mt-1 grid grid-cols-2 gap-6 items-end justify-items-center">
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2">
            <ArrowDown size={18} className="text-emerald-600" />
            <span className="text-3xl font-semibold text-emerald-600">{inbound.toFixed(1)}</span>
          </div>
          <div className="mt-1 text-sm text-gray-500">Mbps IN</div>
        </div>

        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2">
            <ArrowUp size={18} className="text-blue-600" />
            <span className="text-3xl font-semibold text-blue-600">{outbound.toFixed(1)}</span>
          </div>
          <div className="mt-1 text-sm text-gray-500">Mbps OUT</div>
        </div>
      </div>

      {/* 하단: 대역폭 */}
      <div className="mt-4 text-center text-sm text-gray-600">
        대역폭: {bandwidth >= 1000 ? `${bandwidth / 1000}Gbps` : `${bandwidth}Mbps`}
      </div>
    </>
  );
}
