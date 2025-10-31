type Props = {
  leftResult: string | null;
  rightResult: string | null;
};

export function CompareResults({ leftResult, rightResult }: Props) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {[leftResult, rightResult].map((res, i) => (
        <div key={i} className="rounded-xl border bg-white p-4">
          <h3 className="mb-2 text-base font-semibold">결과 {i + 1}</h3>
          <div className="h-60 overflow-auto whitespace-pre-wrap rounded-md border bg-gray-50 p-3 text-sm">
            {res ?? '아직 결과가 없습니다.'}
          </div>
        </div>
      ))}
    </div>
  );
}
