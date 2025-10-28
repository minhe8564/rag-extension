import { FileText } from 'lucide-react';
export default function SelectVectorization() {
  const dummyFiles = [
    {
      id: 1,
      name: '보고서_1.pdf',
      path: '/uploads/보고서_1.pdf',
      currentProgress: 40,
      totalProgress: 100,
    },
    {
      id: 2,
      name: '데이터_분석.csv',
      path: '/uploads/데이터_분석.csv',
      currentProgress: 70,
      totalProgress: 100,
    },
  ];

  return (
    <section className="flex flex-col w-full mt-3 p-4 border rounded-xl bg-white">
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text text-transparent w-fit"
      >
        선택 목록
      </h3>

      <div className="grid grid-cols-8 mt-2 text-sm font-semibold text-gray-800 border-b pb-2 mb-2">
        <span className="col-span-3 text-center">파일명</span>
        <span className="text-center">크기</span>
        <span className="text-center">카테고리</span>
        <span className="text-center">저장위치</span>
        <span className="text-center">현재 진행률</span>
        <span className="text-center">전체 진행률</span>
      </div>

      <div className="flex flex-col mt-2">
        <div />
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 font-medium">
            <div className="w-7 h-7 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
              <FileText size={17} className="text-[var(--color-white)]" />
            </div>
            public
          </div>
        </div>
      </div>
    </section>
  );
}
