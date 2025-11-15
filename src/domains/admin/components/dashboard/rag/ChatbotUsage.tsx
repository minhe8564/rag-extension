import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';
import Select from '@/shared/components/controls/Select';
import { getChatbotUsageTimeSeries } from '@/domains/admin/api/rag.dashboard.api';
import type { chatbotUsageTime } from '@/domains/admin/types/rag.dashboard.types';
import { MousePointerClick } from 'lucide-react';

export default function ChatbotUsage() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const [data, setData] = useState<chatbotUsageTime | null>(null);
  const [period, setPeriod] = useState<'day' | 'week' | 'month'>('day');
  const [_timeframe, setTimeframe] = useState<chatbotUsageTime['timeframe'] | null>(null);
  const [_items, setItems] = useState<chatbotUsageTime['items'] | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getChatbotUsageTimeSeries({ granularity: period });
      setTimeframe(result.timeframe);
      setItems(result.items);
      setData(result);
    };
    fetchData();
  }, [period]);

  useEffect(() => {
    chartRef.current = Highcharts.chart('chatbot-usage-chart', {
      accessibility: {
        enabled: false,
      },
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
        tickPixelInterval: 120,
        minPadding: 0.05,
        maxPadding: 0.05,
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
          marker: { enabled: true, radius: 3 },
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
  }, []);

  const updateChart = (type: 'day' | 'week' | 'month') => {
    setPeriod(type);
    const chart = chartRef.current;
    if (!chart || !data) return;

    const { items } = data;

    if (type === 'day') {
      chart.xAxis[0].update({
        tickInterval: 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.yAxis[0].setTitle({ text: '일별 토큰 사용량' });
    } else if (type === 'week') {
      chart.xAxis[0].update({
        tickInterval: 7 * 24 * 3600 * 1000,
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.yAxis[0].setTitle({ text: '주별 총 토큰 사용량' });
    } else {
      chart.xAxis[0].update({
        tickInterval: 30 * 24 * 3600 * 1000,
        labels: { format: '{value:%m}월', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.yAxis[0].setTitle({ text: '월별 총 토큰 사용량' });
    }

    const seriesData = items.map((item) => [new Date(item.x).getTime(), item.y]);
    chart.series[0].setData(seriesData, true);
  };

  useEffect(() => {
    if (data) {
      updateChart(data.timeframe.granularity as 'day' | 'week' | 'month');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="flex items-start gap-3">
        <MousePointerClick size={20} className="text-red-500 mt-1" />
        <h3 className="text-xl font-semibold text-gray-900">챗봇 사용량 추이</h3>
      </div>
      <p className="mt-0.5 mb-4 text-sm text-gray-500">일별, 주별, 월별 사용량 추이</p>
      <div className="flex items-center justify-between mb-6">
        <div className="ml-auto w-40">
          <Select
            value={period}
            onChange={(v) => updateChart(v as 'day' | 'week' | 'month')}
            options={[
              { label: '일별', value: 'day' },
              { label: '주별', value: 'week' },
              { label: '월별', value: 'month' },
            ]}
          />
        </div>
      </div>

      <div id="chatbot-usage-chart" className="w-full" />
    </div>
  );
}
