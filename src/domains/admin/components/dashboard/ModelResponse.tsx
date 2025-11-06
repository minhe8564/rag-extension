import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import Card from '@/shared/components/Card';
import Select from '@/shared/components/Select';
import type { modelData, modelTokenTime } from '@/domains/admin/types/dashboard.types';
import { getModelTokenUsageTimeSeries } from '@/domains/admin/api/dashboard.api';

export default function ModelResponseTimeChart() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const periods = ['day', 'week', 'month'] as const;
  const [period, setPeriod] = useState<(typeof periods)[number]>('day');
  const [_data, setData] = useState<modelTokenTime | null>(null);
  const [modelsData, setModelsData] = useState<modelData[] | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getModelTokenUsageTimeSeries({ granularity: period });
      console.log('✅ 모델 토큰 응답 시간 시계열 데이터:', result);
      setData(result);
      setModelsData(result.models);
    };
    fetchData();
  }, [period]);

  // 차트 초기화
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

    handlePeriodChange('day');
  }, []);

  // 기간 변경 핸들러
  const handlePeriodChange = (type: (typeof periods)[number]) => {
    setPeriod(type);
    const chart = chartRef.current;
    if (!chart) return;

    // X축 포맷 업데이트
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

    // 모델별 응답 시간 시계열 데이터 반영
    const newSeries = modelsData?.map((model) => ({
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
              { label: '일별', value: 'day' },
              { label: '주별', value: 'week' },
              { label: '월별', value: 'month' },
            ]}
          />
        </div>
      </div>

      <div id="model-response-chart" className="w-full" />
    </Card>
  );
}
