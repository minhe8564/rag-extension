import type { ReactNode } from 'react';

type ProfileInfoCardProps = {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  brand?: 'hebees' | 'retina';
};

export default function ProfileInfoCard({
  icon,
  label,
  value,
  brand = 'retina',
}: ProfileInfoCardProps) {
  const brandColor = brand === 'hebees' ? 'var(--color-hebees)' : 'var(--color-retina)';
  const brandBackgroundColor =
    brand === 'hebees' ? 'var(--color-hebees-bg)' : 'var(--color-retina-bg)';

  return (
    <div
      className={`group flex items-center gap-6 rounded-xl border border-gray-200 bg-white p-4 transition-all duration-200`}
    >
      <div
        className="p-2.5 rounded-lg flex items-center justify-center"
        style={{
          backgroundColor: brandBackgroundColor,
          color: brandColor,
        }}
      >
        {icon}
      </div>

      <div>
        <dt className="text-sm text-gray-500">{label}</dt>
        <dd className="text-base font-semibold text-gray-900 mt-0.5">{value}</dd>
      </div>
    </div>
  );
}
