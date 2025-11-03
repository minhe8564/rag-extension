type ToggleProps = { checked: boolean; onChange: (v: boolean) => void; className?: string };

export function Toggle({ checked, onChange, className = '' }: ToggleProps) {
  const handleToggle = () => onChange(!checked);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={handleToggle}
      onKeyDown={handleKeyDown}
      className={[
        'relative inline-flex items-center h-6 w-11 rounded-full transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--color-hebees)]',
        checked ? 'bg-[var(--color-hebees)]' : 'bg-gray-300',
        className,
      ].join(' ')}
    >
      <span
        className={[
          'absolute left-1 top-1 h-4 w-4 rounded-full bg-white shadow',
          'transition-transform will-change-transform',
          checked ? 'translate-x-5' : 'translate-x-0',
        ].join(' ')}
      />
    </button>
  );
}
