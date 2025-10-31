type Props = {
  leftResult: string | null;
  rightResult: string | null;
};

export function CompareResults({ leftResult, rightResult }: Props) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {[leftResult, rightResult].map((res, i) => (
        <div key={i} className="rounded-2xl border bg-white p-8">
          <h3 className="mb-3 pl-2 text-base font-semibold">
            <span className="bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text text-transparent font-bold">
              HEBEES RAG
            </span>{' '}
            결과 {i + 1}
          </h3>
          <div className="h-60 overflow-auto whitespace-pre-wrap rounded-xl bg-gray-100 p-6 text-sm">
            {res ?? '질문을 입력하고 결과를 확안해보세요.'}
          </div>
        </div>
      ))}
    </div>
  );
}
