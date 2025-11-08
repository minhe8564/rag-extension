import { useEffect, useState, useRef } from 'react';
import Highcharts from 'highcharts';
import _wordcloudInit from 'highcharts/modules/wordcloud';
import Card from '@/shared/components/Card';
import type { frequentKeywords, keywordItem } from '@/domains/admin/types/rag.dashboard.types';
import { getKeywords } from '@/domains/admin/api/rag.dashboard.api';

export default function KeywordMap() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const [_info, setInfo] = useState<frequentKeywords>();
  const [keyword, setKeyword] = useState<keywordItem[]>([]);
  const [starTime, setStartTime] = useState<string>('');
  const [endTime, setEndTime] = useState<string>('');

  useEffect(() => {
    const fetchKeywords = async () => {
      const result = await getKeywords();
      setInfo(result);
      const resultKeywords = result.keywords;
      const startTime = result.timeframe.start;
      const endTime = result.timeframe.end;
      setKeyword(resultKeywords);
      setStartTime(startTime);
      setEndTime(endTime);
    };
    fetchKeywords();
  }, []);

  useEffect(() => {
    if (!keyword || keyword.length === 0) return;

    //  Highcharts용 데이터 변환
    const data = keyword.map((k) => ({
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
        pointFormatter: function (this: Highcharts.Point & { options: { count?: number } }) {
          return `<b>${this.name}</b><br/>등장 횟수: ${this.options.count ?? 0}회`;
        },
      },
      series: [
        {
          type: 'wordcloud',
          name: '키워드 빈도',
          data,
          minFontSize: 8,
          maxFontSize: 60,
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
  }, [keyword]);

  return (
    <Card
      title="최근 주요 키워드"
      subtitle={`${starTime.slice(0, 10)} ~ ${endTime.slice(0, 10)}`}
      className="p-3 h-full flex flex-col"
    >
      <div id="keyword-cloud" className="w-full flex-1 min-h-[100px]" />
    </Card>
  );
}
