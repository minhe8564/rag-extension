import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import Card from '@/shared/components/Card';
import Select from '@/shared/components/Select';

export default function ChatbotUsage() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const periods = ['daily', 'weekly', 'monthly'] as const;
  const [period, setPeriod] = useState<(typeof periods)[number]>('daily');

  // 🔹 더미 데이터 생성 함수
  const generateDummyData = (type: 'daily' | 'weekly' | 'monthly') => {
    const now = new Date();

    if (type === 'daily') {
      // 어제부터 30일치
      const start = new Date(now);
      start.setDate(now.getDate() - 30);
      return {
        timeframe: {
          start: start.toISOString(),
          end: now.toISOString(),
          granularity: 'daily',
        },
        items: Array.from({ length: 30 }, (_, i) => {
          const date = new Date(start);
          date.setDate(start.getDate() + i + 1);
          return {
            x: date.getTime(),
            y: Math.floor(Math.random() * 500) + 200, // 200~700 토큰
          };
        }),
      };
    }

    if (type === 'weekly') {
      // 지난주부터 12주
      const start = new Date(now);
      start.setDate(now.getDate() - 7 * 12);
      return {
        timeframe: {
          start: start.toISOString(),
          end: now.toISOString(),
          granularity: 'weekly',
        },
        items: Array.from({ length: 12 }, (_, i) => {
          const date = new Date(start);
          date.setDate(start.getDate() + i * 7);
          return {
            x: date.getTime(),
            y: Math.floor(Math.random() * 5000) + 1000, // 1,000~6,000
          };
        }),
      };
    }

    // monthly
    const start = new Date(now);
    start.setMonth(now.getMonth() - 12);
    return {
      timeframe: {
        start: start.toISOString(),
        end: now.toISOString(),
        granularity: 'monthly',
      },
      items: Array.from({ length: 12 }, (_, i) => {
        const date = new Date(start);
        date.setMonth(start.getMonth() + i + 1);
        return {
          x: date.getTime(),
          y: Math.floor(Math.random() * 15000) + 5000, // 5,000~20,000
        };
      }),
    };
  };

  // 차트 초기화
  useEffect(() => {
    chartRef.current = Highcharts.chart('chatbot-usage-chart', {
      chart: {
        type: 'line',
        backgroundColor: 'transparent',
        height: 320,
        marginRight: 10,
        animation: true,
      },
      title: { text: '' },
      credits: { enabled: false },
      xAxis: {
        type: 'datetime',
        tickPixelInterval: 150,
        labels: { style: { fontSize: '11px', color: '#6B7280' } },
      },
      yAxis: {
        title: { text: '사용량 (토큰 수)' },
        min: 0,
        labels: { style: { color: '#6B7280' } },
      },
      tooltip: {
        xDateFormat: '%Y-%m-%d',
        pointFormat: '<b>{point.y}</b> 토큰',
      },
      plotOptions: {
        line: {
          color: '#EE5B01',
          lineWidth: 2,
          marker: {
            enabled: true,
            radius: 3,
          },
        },
      },
      series: [
        {
          type: 'line',
          name: '챗봇 사용량',
          color: '#EE5B01',
          data: [],
        },
      ],
    });

    handlePeriodChange('daily'); // 초기 로드
  }, []);

  // 🔹 기간 전환 함수
  const handlePeriodChange = (type: (typeof periods)[number]) => {
    setPeriod(type);
    const chart = chartRef.current;
    if (!chart) return;

    const dummy = generateDummyData(type);

    // 축 포맷 & 단위 변경
    if (type === 'daily') {
      chart.xAxis[0].update({
        tickInterval: 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.yAxis[0].setTitle({ text: '일별 토큰 사용량' });
    } else if (type === 'weekly') {
      chart.xAxis[0].update({
        tickInterval: 7 * 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.yAxis[0].setTitle({ text: '주별 총 토큰 사용량' });
    } else {
      chart.xAxis[0].update({
        tickInterval: 30 * 24 * 3600 * 1000,
        labels: { format: '{value:%Y-%m}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.yAxis[0].setTitle({ text: '월별 총 토큰 사용량' });
    }

    // 데이터 반영
    chart.series[0].setData(
      dummy.items.map((item) => [item.x, item.y]),
      true
    );
  };

  return (
    <Card title="챗봇 사용량 추이" subtitle="일별, 주별, 월별 사용량 추이" className="p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="ml-auto w-40">
          <Select
            value={period}
            onChange={(v) => handlePeriodChange(v as (typeof periods)[number])}
            options={[
              { label: '일별', value: 'daily' },
              { label: '주별', value: 'weekly' },
              { label: '월별', value: 'monthly' },
            ]}
          />
        </div>
      </div>

      <div id="chatbot-usage-chart" className="w-full" />
    </Card>
  );
}
