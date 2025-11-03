const USER_TYPES = [
  { value: 0, label: '개인 안경원' },
  { value: 1, label: '체인 안경원' },
  { value: 2, label: '제조 유통사' },
];

interface UserTypeSelectorProps {
  userType: number;
  setUserType: React.Dispatch<React.SetStateAction<number>>;
}

export default function UserTypeSelector({ userType, setUserType }: UserTypeSelectorProps) {
  return (
    <div className="flex justify-between space-x-2 text-sm">
      {USER_TYPES.map(type => (
        <button
          key={type.value}
          type="button"
          className={`w-1/3 py-2 rounded-md transition-all ${
            userType === type.value
              ? 'bg-[var(--color-hebees-blue)] text-white font-medium'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
          onClick={() => setUserType(type.value)}
        >
          {type.label}
        </button>
      ))}
    </div>
  );
}
