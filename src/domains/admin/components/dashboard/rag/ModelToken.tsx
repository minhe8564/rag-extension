import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import Card from '@/shared/components/Card';
import Select from '@/shared/components/Select';
import type { modelTokenTime, modelData } from '@/domains/admin/types/rag.dashboard.types';
import { getModelTokenUsageTimeSeries } from '@/domains/admin/api/dashboard.api';

export default function ModelUsageChart() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const periods = ['day', 'week', 'month'] as const;
  const [period, setPeriod] = useState<(typeof periods)[number]>('day');
  const [_data, setData] = useState<modelTokenTime | null>(null);
  const [modelsData, setModelsData] = useState<modelData[] | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getModelTokenUsageTimeSeries({ granularity: period });
      console.log('✅ 모델 토큰 사용량 시계열 데이터:', result);
      setData(result);
      setModelsData(result.models);
    };
    fetchData();
  }, [period]);

  // 차트 초기화
  useEffect(() => {
    chartRef.current = Highcharts.chart('model-usage-chart', {
      chart: {
        type: 'areaspline', // 부드러운 누적 면적 그래프
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
        title: { text: '토큰 사용량' },
        labels: { style: { color: '#6B7280' } },
        gridLineColor: '#E5E7EB',
      },
      tooltip: {
        shared: true,
        xDateFormat: '%Y-%m-%d',
        pointFormat: '<b>{series.name}</b>: {point.y} 토큰<br/>',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderColor: '#E5E7EB',
      },
      legend: {
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: { color: '#374151', fontSize: '12px' },
      },
      plotOptions: {
        series: {
          stacking: 'normal', // 누적 영역 설정
        },
        areaspline: {
          fillOpacity: 0.6, // 면적 투명도
          lineWidth: 1.5,
          marker: { enabled: false },
        },
      },
      series: [],
    });

    handlePeriodChange('day');
  }, []);

  // 기간 변경 핸들러
  const handlePeriodChange = (type: (typeof periods)[number]) => {
    setPeriod(type);
    const chart = chartRef.current;
    if (!chart) return;

    // X축 라벨 포맷
    if (type === 'day') {
      chart.xAxis[0].update({
        tickInterval: 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
    } else if (type === 'week') {
      chart.xAxis[0].update({
        tickInterval: 7 * 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
    } else {
      chart.xAxis[0].update({
        tickInterval: 30 * 24 * 3600 * 1000,
        labels: { format: '{value:%m}월', style: { fontSize: '11px', color: '#6B7280' } },
      });
    }

    // 모델별 누적 면적 그래프 시리즈 생성
    const newSeries = modelsData?.map((model) => ({
      name: model.modelName,
      type: 'areaspline' as const,
      data: model.usageTokens.map((point) => [point.x, point.y]),
    }));

    chart.update({ series: newSeries }, true, true);
  };

  return (
    <Card title="모델별 토큰 사용량" subtitle="일별, 주별, 월별 토큰 사용량 추이" className="p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="ml-auto w-40">
          <Select
            value={period}
            onChange={(v) => handlePeriodChange(v as (typeof periods)[number])}
            options={[
              { label: '일별', value: 'day' },
              { label: '주별', value: 'week' },
              { label: '월별', value: 'month' },
            ]}
          />
        </div>
      </div>

      <div id="model-usage-chart" className="w-full" />
    </Card>
  );
}
