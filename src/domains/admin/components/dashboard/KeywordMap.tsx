import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import 'highcharts/modules/wordcloud';

type WordData = { name: string; weight: number };

export default function KeywordMap() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const [keywords, setKeywords] = useState<WordData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ✅ API 연결 시도 (현재 주석처리)
  // useEffect(() => {
  //   setIsLoading(true);
  //   fetch('http://localhost:8000/api/keywords') // ← 실제 API 주소로 변경
  //     .then((res) => {
  //       if (!res.ok) throw new Error('네트워크 응답 오류');
  //       return res.json();
  //     })
  //     .then((data: WordData[]) => {
  //       setKeywords(data);
  //       setError(null);
  //     })
  //     .catch((err) => {
  //       console.error('키워드 데이터 불러오기 실패:', err);
  //       setError('데이터 불러오기 실패');
  //     })
  //     .finally(() => setIsLoading(false));
  // }, []);

  // ✅ 더미 데이터 (API 연동 전용 임시)
  useEffect(() => {
    const dummyData: WordData[] = [
      { name: '챗봇', weight: 25 },
      { name: '사용자', weight: 18 },
      { name: 'AI', weight: 22 },
      { name: '응답', weight: 14 },
      { name: '질문', weight: 19 },
      { name: '대화', weight: 16 },
      { name: '프롬프트', weight: 12 },
      { name: '피드백', weight: 17 },
      { name: '서비스', weight: 10 },
      { name: '성능', weight: 8 },
      { name: '토큰', weight: 11 },
      { name: '응답시간', weight: 13 },
    ];
    setKeywords(dummyData);
  }, []);

  // ✅ 차트 생성
  useEffect(() => {
    if (!keywords.length || isLoading) return;

    const maxWeight = Math.max(...keywords.map((d) => d.weight));

    chartRef.current = Highcharts.chart('keyword-map', {
      chart: { backgroundColor: 'transparent' },
      title: { text: '' },
      credits: { enabled: false },
      tooltip: {
        backgroundColor: '#fff',
        borderColor: '#E5E7EB',
        borderRadius: 10,
        borderWidth: 1,
        shadow: false,
        style: { color: '#111827', fontSize: '12px' },
        pointFormat: '<b>{point.name}</b>: {point.weight}회',
      },
      series: [
        {
          type: 'wordcloud',
          name: '키워드 빈도수',
          data: keywords,
          rotation: { from: -20, to: 20, orientations: 5 },
          spiral: 'rectangular',
          minFontSize: 12,
          maxFontSize: 42,

          // 🎨 가중치 기반 색상 밝기
          colors: keywords.map((d) => {
            const ratio = d.weight / maxWeight;
            const base = [150, 37, 122]; // var(--color-hebees)
            return `rgb(${base[0]}, ${base[1] + 80 * ratio}, ${base[2] + 80 * ratio})`;
          }),

          style: {
            fontFamily: 'Pretendard, sans-serif',
            fontWeight: '600',
            textOutline: 'none',
            transition: 'transform 0.25s ease, color 0.25s ease',
            cursor: 'pointer',
          },

          states: {
            hover: {
              halo: { size: 10, attributes: { opacity: 0.3 } },
              brightness: 0.15,
            },
          },

          events: {
            mouseOver: function (e) {
              const el = e?.target?.graphic?.element as SVGElement | undefined;
              if (el) el.style.transform = 'scale(1.25)';
            },
            mouseOut: function (e) {
              const el = e?.target?.graphic?.element as SVGElement | undefined;
              if (el) el.style.transform = 'scale(1.0)';
            },
            click: function (e) {
              console.log(`🟣 클릭된 키워드: ${e.point.name}`);
            },
          },
        } as Highcharts.SeriesWordcloudOptions,
      ],
    });

    return () => chartRef.current?.destroy();
  }, [keywords, isLoading]);

  // ✅ 로딩 / 에러 상태 표시
  if (isLoading) {
    return (
      <div className="flex items-center justify-center w-full h-[320px] rounded-xl border">
        <p className="text-gray-500 text-sm">키워드 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center w-full h-[320px] rounded-xl border">
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full p-4 border border-gray-200 rounded-xl bg-white transition-all">
      <h2 className="text-xl font-bold text-gray-800 mb-2">키워드 맵</h2>
      <p className="text-sm text-gray-500 mb-3">최근 자주 등장한 주요 키워드</p>

      <div
        id="keyword-map"
        className="w-full h-[340px] border border-gray-200 rounded-xl bg-white shadow-sm"
      />
    </div>
  );
}
