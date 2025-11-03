import { useState, useEffect, useRef } from 'react';
import { Users, FileText, TriangleAlert, TrendingUp, TrendingDown } from 'lucide-react';
import Card from '@/shared/components/Card';

export default function NumberBoard() {
  const [data, setData] = useState({
    currentUsers: 24,
    uploadedDocs: 58,
    errorCount: 3,
  });

  const [displayData, setDisplayData] = useState({ ...data });
  const [prevData, setPrevData] = useState({ ...data });
  const [animatingKey, setAnimatingKey] = useState<string | null>(null);

  const yesterday = {
    currentUsers: 20,
    uploadedDocs: 40,
    errorCount: 5,
  };

  const animRefs = useRef<Record<string, number | null>>({
    currentUsers: null,
    uploadedDocs: null,
    errorCount: null,
  });

  const formatNumber = (n: number | undefined) => (n ?? 0).toLocaleString();

  useEffect(() => {
    const interval = setInterval(() => {
      const newData = {
        currentUsers: Math.floor(Math.random() * 100) + 10,
        uploadedDocs: Math.floor(Math.random() * 200),
        errorCount: Math.floor(Math.random() * 8),
      };
      animateNumbers(newData);
    }, 10000);
    return () => clearInterval(interval);
  }, [displayData]);

  const animateNumbers = (newData: typeof data) => {
    (Object.keys(newData) as (keyof typeof newData)[]).forEach((key) => {
      const start = displayData[key] ?? 0;
      const end = newData[key];
      const duration = 1000;
      const startTime = performance.now();

      setPrevData((prev) => ({ ...prev, [key]: start }));
      setAnimatingKey(key);

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
          setTimeout(() => setAnimatingKey(null), 300);
        }
      };
      animRefs.current[key] = requestAnimationFrame(animate);
    });

    setData(newData);
  };

  const renderCard = (
    key: keyof typeof data,
    title: string,
    icon: JSX.Element,
    total: number,
    totalLabel: string
  ) => {
    const delta = (displayData[key] ?? 0) - (yesterday[key] ?? 0);
    const IconArrow = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : null;
    const sign = delta > 0 ? '+' : '';
    const color = delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-500';

    return (
      <Card title="" className="p-4 sm:p-5">
        {/* 헤더 */}
        <div className="mb-3 flex items-center gap-2">
          {icon}
          <span className="text-lg font-bold text-gray-900">{title}</span>
        </div>

        {/* 메인 숫자 */}
        <div className="flex flex-col  space-y-1">
          <div className="flex items-end gap-0.5">
            <div className="relative h-9 overflow-hidden w-16 sm:w-20">
              {/* 이전 값 */}
              <p
                className={`absolute left-0 right-0 text-2xl sm:text-3xl font-extrabold text-gray-900 transition-all duration-500 ${
                  animatingKey === key ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'
                }`}
              >
                {formatNumber(prevData[key])}
              </p>
              {/* 새 값 */}
              <p
                className={`absolute left-4 right-0 text-2xl sm:text-3xl font-extrabold text-gray-900 transition-all duration-500 ${
                  animatingKey === key ? 'translate-y-full opacity-0' : 'translate-y-0 opacity-100'
                }`}
              >
                {formatNumber(displayData[key])}
              </p>
            </div>
            <span className="text-sm text-gray-400 mx-0.5">/</span>
            <span className="text-xs text-gray-500 font-medium">
              {totalLabel} {formatNumber(total)}
            </span>
          </div>

          <div className=" flex items-center">
            <div className="flex items-center gap-2 border rounded-lg px-2 py-1.5 shadow-sm bg-white">
              {IconArrow && (
                <IconArrow
                  size={12}
                  className={`${delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-600' : 'text-gray-400'}`}
                />
              )}
              <span className="text-gray-600 text-xs sm:text-sm">하루 전 대비</span>
              <span className={`text-xs sm:text-sm font-semibold ${color}`}>
                {sign}
                {Math.abs(delta)}
              </span>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  return (
    <section className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-5 my-4 max-w-5xl mx-auto">
      {renderCard(
        'currentUsers',
        '현재 사용자 수',
        <div className="h-12 w-12 rounded-lg bg-[var(--color-hebees-blue-bg)] flex items-center justify-center shadow-sm">
          <Users size={26} className="text-[var(--color-hebees-blue)]" />
        </div>,
        5000,
        '총'
      )}
      {renderCard(
        'uploadedDocs',
        '오늘 업로드 문서 수',
        <div className="h-12 w-12 rounded-lg bg-[var(--color-hebees-bg)] flex items-center justify-center shadow-sm">
          <FileText size={26} className="text-[var(--color-hebees)]" />
        </div>,
        3705,
        '총'
      )}
      {renderCard(
        'errorCount',
        '오늘 오류 발생',
        <div className="h-12 w-12 rounded-lg bg-red-50 flex items-center justify-center shadow-sm">
          <TriangleAlert size={26} className="text-red-500" />
        </div>,
        156,
        '총'
      )}
    </section>
  );
}
