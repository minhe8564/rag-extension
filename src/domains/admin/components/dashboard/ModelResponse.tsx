import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import Card from '@/shared/components/Card';
import Select from '@/shared/components/Select';

export default function ModelResponseTimeChart() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const periods = ['daily', 'weekly', 'monthly'] as const;
  const [period, setPeriod] = useState<(typeof periods)[number]>('daily');

  // 🔹 더미 데이터 생성 함수 (API 구조 기반)
  const generateDummyResponseData = (type: 'daily' | 'weekly' | 'monthly') => {
    const now = new Date();
    const models = [
      { modelId: 'gpt-4o-mini', modelName: 'GPT-4o Mini' },
      { modelId: 'gpt-4o', modelName: 'GPT-4o' },
      { modelId: 'gpt-3.5', modelName: 'GPT-3.5 Turbo' },
    ];

    let length = 0;
    let interval = 0;
    let granularity = '';

    if (type === 'daily') {
      length = 7;
      interval = 24 * 3600 * 1000;
      granularity = 'daily';
    } else if (type === 'weekly') {
      length = 5;
      interval = 7 * 24 * 3600 * 1000;
      granularity = 'weekly';
    } else {
      length = 3;
      interval = 30 * 24 * 3600 * 1000;
      granularity = 'monthly';
    }

    const start = new Date(now.getTime() - interval * length);
    const timeframe = {
      start: start.toISOString(),
      end: now.toISOString(),
      granularity,
    };

    // 모델별 시계열 데이터
    const modelData = models.map((model) => ({
      modelId: model.modelId,
      modelName: model.modelName,
      usageTokens: Array.from({ length }, (_, i) => ({
        x: start.getTime() + interval * (i + 1),
        y: Math.floor(Math.random() * 5000) + 1000, // 예시용 (token용)
      })),
      averageResponseTimesMs: Array.from({ length }, (_, i) => ({
        x: start.getTime() + interval * (i + 1),
        y: Math.floor(Math.random() * 400) + 150, // 150~550ms
      })),
    }));

    return { timeframe, models: modelData };
  };

  // 🔹 차트 초기화
  useEffect(() => {
    chartRef.current = Highcharts.chart('model-response-chart', {
      chart: {
        type: 'line',
        backgroundColor: 'transparent',
        height: 300,
        animation: true,
      },
      title: { text: '' },
      credits: { enabled: false },
      xAxis: {
        type: 'datetime',
        labels: { style: { fontSize: '11px', color: '#6B7280' } },
      },
      yAxis: {
        title: { text: '평균 응답 시간 (ms)' },
        labels: { style: { color: '#6B7280' } },
        gridLineColor: '#E5E7EB',
      },
      tooltip: {
        shared: true,
        xDateFormat: '%Y-%m-%d',
        pointFormat: '<b>{series.name}</b>: {point.y} ms<br/>',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderColor: '#E5E7EB',
      },
      legend: {
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: { color: '#374151', fontSize: '12px' },
      },
      plotOptions: {
        line: {
          lineWidth: 2,
          marker: { enabled: true, radius: 3 },
        },
      },
      series: [],
    });

    handlePeriodChange('daily'); // 초기: 일별
  }, []);

  // 🔹 기간 변경 핸들러
  const handlePeriodChange = (type: (typeof periods)[number]) => {
    setPeriod(type);
    const chart = chartRef.current;
    if (!chart) return;

    const dummy = generateDummyResponseData(type);

    // X축 포맷 업데이트
    if (type === 'daily') {
      chart.xAxis[0].update({
        tickInterval: 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
    } else if (type === 'weekly') {
      chart.xAxis[0].update({
        tickInterval: 7 * 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
    } else {
      chart.xAxis[0].update({
        tickInterval: 30 * 24 * 3600 * 1000,
        labels: { format: '{value:%Y-%m}', style: { fontSize: '11px', color: '#6B7280' } },
      });
    }

    // 모델별 응답 시간 시계열 데이터 반영
    const newSeries = dummy.models.map((model) => ({
      name: model.modelName,
      type: 'line' as const,
      data: model.averageResponseTimesMs.map((point) => [point.x, point.y]),
    }));

    chart.update({ series: newSeries }, true, true);
  };

  return (
    <Card
      title="모델별 평균 응답 시간"
      subtitle="일별, 주별, 월별 평균 응답 시간 추이"
      className="p-4"
    >
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

      <div id="model-response-chart" className="w-full" />
    </Card>
  );
}
