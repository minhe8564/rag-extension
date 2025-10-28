import {FolderOpen} from 'lucide-react';
export default function StorageLocation() {
  return (
    <section className="flex flex-col w-1/2 p-4 border border-gray-200 rounded-xl bg-white">
      {/* 제목 */}
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text text-transparent w-fit"
      >
        저장 위치
      </h3>

      {/* 폴더 리스트 */}
      <div className="flex flex-col gap-3">
        {/* 폴더 - public */}
        <div className="border rounded-lg p-3 hover:bg-[var(--color-hebees-bg)]/50 transition">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 font-medium text-gray-800">
              <div className="w-8 h-8 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                <FolderOpen className="text-[var(--color-white)] w-5 h-5" />
              </div>
              public
            </div>
            <input type="checkbox" className="accent-[var(--color-hebees)]" />
          </div>

          {/* 파일 목록 */}
          <ul className="pl-8 text-sm text-gray-600">
            <li className="flex justify-between py-1 border-b border-gray-100">
              헵비스_스타터 실험 플랫폼 RAG 기본 시 검증 개발 1
              <button className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-blue)]">
                조회
              </button>
            </li>
            <li className="flex justify-between py-1">
              헵비스_스타터 실험 플랫폼 RAG 기본 시 검증 개발 2
              <button className="text-[var(--color-hebees)] hover:text-[var(--color-hebees-blue)]">
                조회
              </button>
            </li>
          </ul>

          {/* 페이지네이션 */}
          <div className="flex justify-center gap-3 mt-2 text-xs text-gray-500">
            <button className="hover:text-[var(--color-hebees)]">이전</button>
            <span>1</span>
            <span>2</span>
            <button className="hover:text-[var(--color-hebees)]">다음</button>
          </div>
        </div>

        {/* 폴더 - hebees */}
        <div className="border rounded-lg p-3 hover:bg-[var(--color-hebees-bg)]/50 transition">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-medium text-gray-800">
              <div className="w-8 h-8 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                <FolderOpen className="text-[var(--color-white)] w-5 h-5" />
              </div>
              hebees
            </div>
            <input type="checkbox" className="accent-[var(--color-hebees)]" />
          </div>
        </div>
      </div>
    </section>
  );
}
