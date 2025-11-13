import React from 'react';
import type { FlowStepId } from '@/shared/components/rag-pipeline/PipelineFlow';

type SectionHeaderProps = {
  id: FlowStepId;
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  onClick: (id: FlowStepId) => void;
};

export default function SectionHeader({ id, title, subtitle, icon, onClick }: SectionHeaderProps) {
  return (
    <div
      className="
        mb-10 flex cursor-pointer items-start gap-4 transition-all
        hover:-translate-y-[1px] hover:opacity-95
      "
      onClick={() => onClick(id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onClick(id)}
    >
      {icon && (
        <div
          className="
            mt-0.5 flex h-14 w-14 items-center justify-center 
            rounded-xl bg-[#F7F8FA]
            text-[var(--color-hebees)]
            shadow-sm border border-gray-200
          "
        >
          <div className="w-8 h-8 [&>img]:w-full [&>img]:h-full [&>svg]:w-full [&>svg]:h-full">
            {icon}
          </div>
        </div>
      )}

      <div>
        <h3 className="text-xl font-semibold leading-tight text-gray-900">{title}</h3>
        {subtitle && <p className="mt-1 text-sm leading-relaxed text-gray-500">{subtitle}</p>}
      </div>
    </div>
  );
}
