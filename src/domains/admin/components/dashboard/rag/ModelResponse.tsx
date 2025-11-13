import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import Select from '@/shared/components/Select';
import type { modelData, modelTokenTime } from '@/domains/admin/types/rag.dashboard.types';
import { getModelTokenUsageTimeSeries } from '@/domains/admin/api/rag.dashboard.api';
import { Clock } from 'lucide-react';

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
      setModelsData(result.model);
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
        itemStyle: { color: '#374151', fontSize: '10px' },
      },
      plotOptions: {
        line: {
          lineWidth: 2,
          marker: { enabled: true, radius: 3 },
        },
      },
      series: [],
    });
  }, []);

  useEffect(() => {
    if (!modelsData || !chartRef.current) return;

    const newSeries: Highcharts.SeriesOptionsType[] = modelsData.map((m) => ({
      name: m.modelName,
      type: 'line',
      data: m.averageResponseTimeMs.map((p) => [p.x, p.y]),
    }));

    setTimeout(() => {
      chartRef.current?.update({ series: newSeries as Highcharts.SeriesOptionsType[] }, true, true);
    }, 0);
  }, [modelsData, chartRef.current]);

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
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="flex items-start gap-3">
        <Clock size={20} className="text-red-500 mt-1" />
        <h3 className="text-xl font-semibold text-gray-900">모델별 평균 응답 시간</h3>
      </div>
      <p className="mt-0.5 mb-4 text-sm text-gray-500">일별, 주별, 월별 사용량 추이</p>
      <div className="flex items-center justify-between mb-6">
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
    </div>
  );
}
