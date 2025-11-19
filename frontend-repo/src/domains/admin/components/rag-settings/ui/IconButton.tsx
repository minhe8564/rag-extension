import Tooltip from '@/shared/components/controls/Tooltip';

type IconButtonProps = {
  title: string;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
};

export function IconButton({
  title,
  onClick,
  children,
  className = '',
  disabled = false,
}: IconButtonProps) {
  return (
    <Tooltip content={title} side="bottom" offset={6}>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className={[
          'inline-flex h-8 w-8 items-center justify-center rounded-md border bg-white transition-colors',
          'text-gray-500 hover:bg-gray-50 hover:text-gray-800',
          disabled && 'opacity-50 cursor-not-allowed',
          className,
        ].join(' ')}
      >
        {children}
      </button>
    </Tooltip>
  );
}
