import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface FormInputProps {
  type: 'text' | 'email' | 'password' | 'number' | 'tel';
  placeholder?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
}

export default function FormInput({
  type,
  placeholder,
  value,
  onChange,
  required = false,
}: FormInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const inputType = type === 'password' ? (showPassword ? 'text' : 'password') : type;
  const inputClassName =
    'w-full rounded-md border border-gray-300 p-3 text-sm outline-none focus:border-[var(--color-hebees-blue)] focus:bg-[var(--color-hebees-blue-bg)] focus:ring-0';

  return (
    <div className="relative">
      <input
        className={`${inputClassName} ${type === 'password' ? 'pr-10' : ''}`}
        type={inputType}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
      />

      {type === 'password' && (
        <button
          type="button"
          className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400"
          onClick={() => setShowPassword(!showPassword)}
          aria-label={showPassword ? '비밀번호 숨기기' : '비밀번호 보기'}
        >
          {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
        </button>
      )}
    </div>
  );
}
