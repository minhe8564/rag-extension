import React, { useState, forwardRef } from 'react';
import { Eye, EyeOff } from 'lucide-react';

type BasicTypes = 'text' | 'email' | 'password' | 'number' | 'tel';

export interface FormInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'value' | 'onChange'> {
  type: BasicTypes;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  showPasswordToggle?: boolean;
  containerClassName?: string;
  inputClassName?: string;
}

const FormInput = forwardRef<HTMLInputElement, FormInputProps>(function FormInput(
  {
    type,
    value,
    onChange,
    placeholder,
    required = false,
    showPasswordToggle = true,
    containerClassName,
    inputClassName,
    ...rest
  },
  ref
) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === 'password';
  const resolvedType = isPassword ? (showPassword ? 'text' : 'password') : type;

  const baseCls =
    'w-full rounded-md border border-gray-300 p-3 text-sm outline-none ' +
    'focus:border-[var(--color-hebees-blue)] focus:bg-[var(--color-hebees-blue-bg)] focus:ring-0';

  return (
    <div className={`relative ${containerClassName ?? ''}`}>
      <input
        ref={ref}
        className={`${baseCls} ${isPassword && showPasswordToggle ? 'pr-10' : ''} ${inputClassName ?? ''}`}
        type={resolvedType}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        {...rest}
      />

      {isPassword && showPasswordToggle && (
        <button
          type="button"
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
          onClick={() => setShowPassword(v => !v)}
          aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
          tabIndex={-1}
        >
          {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
        </button>
      )}
    </div>
  );
});

export default FormInput;
