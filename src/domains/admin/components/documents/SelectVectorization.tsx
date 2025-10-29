import { FileText, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useState } from 'react';
import VecProcess from './VecProcess';
export default function SelectVectorization() {
  const dummyFiles = [
    {
      id: 1,
      name: 'hebees_플랫폼_기획서.pdf',
      size: '2.4MB',
      category: '문서',
      storage: 'public',
      currentProgress: '데이터 정제 43%',
      totalProgress: 6,
    },
    {
      id: 2,
      name: 'hebees_AI_모델_실험결과.csv',
      size: '1.1MB',
      category: '데이터',
      storage: 'public',
      currentProgress: '임베딩 생성',
      totalProgress: 33,
    },
    {
      id: 3,
      name: 'hebees_RAG_API_설계서.docx',
      size: '3.8MB',
      category: '문서',
      storage: 'public',
      currentProgress: '임베딩 생성',
      totalProgress: 56,
    },
    {
      id: 4,
      name: 'hebees_챗봇_테스트_로그.json',
      size: '4.2MB',
      category: '로그',
      storage: 'internal',
      currentProgress: '시작 전',
      totalProgress: 0,
    },
    {
      id: 5,
      name: 'hebees_UI_디자인_리뷰.png',
      size: '950KB',
      category: '이미지',
      storage: 'public',
      currentProgress: '완료',
      totalProgress: 100,
    },
    {
      id: 6,
      name: 'hebees_챗봇 리뷰.png',
      size: '440KB',
      category: '로그',
      storage: 'public',
      currentProgress: '시작 전',
      totalProgress: 0,
    },
  ];
  //   const [uploadFiles, setUploadFiles] = useState(dummyFiles);
  //   const [selectedFiles, setSelectedFiles] = useState<FileType[]>([]);
  //   const [storageMap, setStorageMap] = useState<Record<number,string>>({});

  //   const handleUpload = (newFiles: FileType) => {
  //     setUploadFiles((prev) => [...prev, newFiles]);
  //   }

  //   const handleSelectFile = (file: FileType) => {
  //     setSelectedFiles(prev => {
  //     // 이미 선택된 경우 → 해제
  //     if (prev.find(f => f.id === file.id)) {
  //       return prev.filter(f => f.id !== file.id);
  //     }
  //     // 처음 선택된 경우 → 추가
  //     return [...prev, file];
  //   });
  // };

  //   const handleStorageChange = (id: number, location: string) =>{
  //     setStorageMap(prev =>({ ...prev, [id]: location }))
  //   }

  //   const handleRemove = (id: number) => {
  //     setSelectedFiles((prev) => prev.filter((file) => file.id !== id));
  //     setStorageMap((prev) => {
  //       const updatedMap = { ...prev };
  //       delete updatedMap[id];
  //       return updatedMap;
  //     });
  //   };

  const itemsPerPage = 5;
  const [currentPage, setCurrentPage] = useState(1);

  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentFiles = dummyFiles.slice(startIndex, startIndex + itemsPerPage);
  const totalPages = Math.ceil(dummyFiles.length / itemsPerPage);

  const [selectedFile, _setSelectedFile] = useState(dummyFiles[0]);
  return (
    <section className="flex flex-col w-full mt-3 p-4 mb-10 border rounded-xl bg-white">
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text text-transparent w-fit"
      >
        선택 목록
      </h3>

      <div className="grid grid-cols-8 mt-2 text-sm font-semibold text-gray-800 border-b pb-2">
        <span className="col-span-3 text-center">파일명</span>
        <span className="text-center">크기</span>
        <span className="text-center">카테고리</span>
        <span className="text-center">저장위치</span>
        <span className="text-center">현재 진행률</span>
        <span className="text-center">전체 진행률</span>
      </div>

      <div className="flex flex-col min-h-[200px]">
        {currentFiles.map((file) => (
          <div
            key={file.id}
            className="grid grid-cols-8 items-center text-sm pt-2 border-b last:border-none"
          >
            <div className="col-span-3 flex items-center gap-2 text-xs font-regular pl-2">
              <button>
                <X size={17} className="text-[var(--color-hebees)]" />
              </button>
              <div className="w-7 h-7 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                <FileText size={17} className="text-[var(--color-white)]" />
              </div>
              {file.name}
            </div>

            {/* 크기 */}
            <span className="text-center text-xs font-regular">{file.size}</span>

            {/* 카테고리 */}
            <span className="text-center text-xs font-regular">{file.category}</span>

            {/* 저장 위치 */}
            <span className="text-center text-xs font-regular">{file.storage}</span>

            {/* 현재 진행률 */}
            <span className="text-center text-xs font-regular">{file.currentProgress}%</span>

            {/* 전체 진행률 */}
            <span className="text-center text-xs font-regular">{file.totalProgress}%</span>
          </div>
        ))}
      </div>

      {/* 페이지네이션 */}
      <div className="flex justify-center gap-2 items-center mt-4">
        <button
          onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
          disabled={currentPage === 1}
          className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40 disabled:hover:text-gray-600"
        >
          <ChevronLeft size={10} />
          <span>이전</span>
        </button>

        <span className="text-xs font-medium">
          {currentPage} / {totalPages}
        </span>

        <button
          onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
          disabled={currentPage === totalPages}
          className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-30 disabled:hover:text-gray-600"
        >
          <span>다음</span>
          <ChevronRight size={10} />
        </button>
      </div>
      <div className="flex justify-center">
        <button
          onClick={() => console.log('벡터화 실행')}
          className="
            mt-6
            mb-4
            px-10 py-2
            text-white font-semibold
            rounded-md
            bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)]
            hover:opacity-90
            transition
            shadow-md
          "
        >
          벡터화 실행
        </button>
      </div>
      <VecProcess selectedFile={selectedFile} />
    </section>
  );
}
