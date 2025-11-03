import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import _wordcloudInit from 'highcharts/modules/wordcloud';
import Card from '@/shared/components/Card';

export default function KeywordCloud() {
  const chartRef = useRef<Highcharts.Chart | null>(null);

  // 더미
  useEffect(() => {
    const dummyResponse = {
      timeframe: {
        start: new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString(),
        end: new Date().toISOString(),
      },
      keywords: [
        { text: '시력검사', count: 410, weight: 0.9 },
        { text: '렌즈추천', count: 385, weight: 0.93 },
        { text: '누진렌즈', count: 350, weight: 0.88 },
        { text: '도수측정', count: 320, weight: 0.12 },
        { text: '안경테', count: 295, weight: 0.98 },
        { text: '렌즈교체', count: 260, weight: 0.83 },
        { text: '시야흐림', count: 235, weight: 0.78 },
        { text: '난시교정', count: 210, weight: 0.54 },
        { text: '렌즈두께', count: 180, weight: 0.38 },
        { text: '아동안경', count: 165, weight: 0.45 },
        { text: '렌즈세척', count: 150, weight: 0.3 },
        { text: '눈피로', count: 125, weight: 0.15 },
        { text: '렌즈코팅', count: 95, weight: 0.38 },
        { text: '자외선차단', count: 80, weight: 0.13 },
        { text: '맞춤안경', count: 70, weight: 0.3 },
      ],
    };

    //  Highcharts용 데이터 변환
    const data = dummyResponse.keywords.map((k) => ({
      name: k.text,
      weight: k.weight,
      count: k.count,
    }));

    //  차트 생성
    chartRef.current = Highcharts.chart('keyword-cloud', {
      chart: {
        backgroundColor: 'transparent',
      },
      title: { text: '' },
      credits: { enabled: false },
      tooltip: {
        backgroundColor: '#fff',
        borderColor: '#E5E7EB',
        borderRadius: 10,
        borderWidth: 1,
        shadow: false,
        style: { color: '#111827', fontSize: '12px' },
        pointFormatter: function (this: Highcharts.Point & { count: number }) {
          return `<b>${this.name}</b><br/>등장 횟수: ${this.count}회`;
        },
      },
      series: [
        {
          type: 'wordcloud',
          name: '키워드 빈도',
          data,
          minFontSize: 10,
          maxFontSize: 80,
          spiral: 'rectangular',
          rotation: { from: 0, to: 0, orientations: 6 },
          placementStrategy: 'center',
          padding: 2,
          center: ['50%', '50%'],
          colors: undefined,
          style: {
            fontFamily: 'Pretendard, sans-serif',
            fontWeight: '600',
            textOutline: 'none',
            cursor: 'pointer',
            transition: 'transform 0.25s ease, color 0.25s ease',
          },
          states: {
            hover: {
              halo: { size: 8, attributes: { opacity: 0.3 } },
              brightness: 0.15,
            },
          },
        } as Highcharts.SeriesWordcloudOptions,
      ],
    });

    return () => chartRef.current?.destroy();
  }, []);

  return (
    <Card title="최근 주요 키워드" subtitle="가중치 기반 워드클라우드" className="p-4">
      <div id="keyword-cloud" className="w-full h-[360px]" />
    </Card>
  );
}
