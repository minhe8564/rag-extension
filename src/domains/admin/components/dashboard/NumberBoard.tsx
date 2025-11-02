import { useState, useEffect, useRef } from 'react';

export default function NumberBoard() {
  const [data, setData] = useState({
    currentUsers: 12,
    totalUsers: 128,
    uploadedDocs: 34,
    errorCount: 1,
  });

  const [displayData, setDisplayData] = useState({ ...data });
  const [prevData, setPrevData] = useState({ ...data });
  const [animatingKey, setAnimatingKey] = useState<string | null>(null);

  const animRefs = useRef<Record<string, number | null>>({
    currentUsers: null,
    totalUsers: null,
    uploadedDocs: null,
    errorCount: null,
  });

  // 더미 데이터 (SSE 연결 전 시뮬레이션)
  useEffect(() => {
    const interval = setInterval(() => {
      const newData = {
        currentUsers: Math.floor(Math.random() * 50) + 10,
        totalUsers: 200,
        uploadedDocs: Math.floor(Math.random() * 100),
        errorCount: Math.floor(Math.random() * 5),
      };
      animateNumbers(newData);
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  // 숫자 애니메이션 로직
  const animateNumbers = (newData: typeof data) => {
    (Object.keys(newData) as (keyof typeof newData)[]).forEach((key) => {
      const start = displayData[key] ?? 0;
      const end = newData[key];
      const duration = 800;
      const startTime = performance.now();

      if (start !== end) {
        setPrevData((prev) => ({ ...prev, [key]: start }));
        setAnimatingKey(key); // 해당 key만 스와이프 모션
      }

      if (animRefs.current[key]) cancelAnimationFrame(animRefs.current[key]!);

      const animate = (time: number) => {
        const progress = Math.min((time - startTime) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.floor(start + (end - start) * eased);
        setDisplayData((prev) => ({ ...prev, [key]: value }));

        if (progress < 1) {
          animRefs.current[key] = requestAnimationFrame(animate);
        } else {
          animRefs.current[key] = null;
          setDisplayData((prev) => ({ ...prev, [key]: end }));
          setTimeout(() => setAnimatingKey(null), 500); // 모션 끝나면 초기화
        }
      };
      animRefs.current[key] = requestAnimationFrame(animate);
    });

    setData(newData);
  };

  const isLoading = Object.values(data).some((v) => v === null);

  return (
    <section className="flex justify-between gap-4 my-4">
      {[
        { title: '현재 사용자 수', key: 'currentUsers' },
        { title: '전체 사용자 수', key: 'totalUsers' },
        { title: '오늘 업로드 문서 수', key: 'uploadedDocs' },
        { title: '오늘 오류 발생', key: 'errorCount' },
      ].map((item) => (
        <div
          key={item.key}
          className="flex flex-col w-1/4 p-4 border border-gray-200 rounded-xl shadow-sm bg-white"
        >
          <h2 className="text-base font-semibold text-gray-700 mb-1">{item.title}</h2>

          {isLoading ? (
            <div className="w-1/2 h-6 bg-gray-200 animate-pulse rounded-md" />
          ) : (
            <div className="relative h-8 overflow-hidden">
              {/* 이전 숫자 (위로 사라짐) */}
              <p
                className={`absolute left-0 right-0 text-2xl font-bold text-gray-800 transition-all duration-300 ${
                  animatingKey === item.key
                    ? '-translate-y-full opacity-0'
                    : 'translate-y-0 opacity-100'
                }`}
              >
                {prevData[item.key as keyof typeof prevData]}
              </p>

              {/* 새 숫자 (아래에서 올라옴) */}
              <p
                className={`absolute left-0 right-0 text-2xl font-bold text-gray-800 transition-all duration-300 ${
                  animatingKey === item.key
                    ? 'translate-y-0 opacity-100'
                    : 'translate-y-full opacity-0'
                }`}
              >
                {displayData[item.key as keyof typeof displayData]}
              </p>
            </div>
          )}
        </div>
      ))}
    </section>
  );
}
