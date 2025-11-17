import { useEffect, useState, useRef } from 'react';
import Highcharts from 'highcharts';
import _Heatmap from 'highcharts/modules/heatmap';
import { getChatbotUsageHeatmap } from '@/domains/admin/api/rag.dashboard.api';
import type {
  chatbotHeatmapTimeframe,
  chatbotHeatmapLabels,
} from '@/domains/admin/types/rag.dashboard.types';
import { FolderKanban } from 'lucide-react';

function niceRound(num: number) {
  if (num === 0) return 0;
  const magnitude = Math.pow(10, Math.floor(Math.log10(num)) - 1);
  return Math.round(num / magnitude) * magnitude;
}

export default function WeeklyTimeHeatmap() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const [_timeframe, setTimeframe] = useState<chatbotHeatmapTimeframe | null>(null);
  const [label, setLabel] = useState<chatbotHeatmapLabels | null>(null);
  const [cells, setCells] = useState<Array<Array<number>>>([]);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getChatbotUsageHeatmap();
      setTimeframe(result.timeframe);
      setLabel(result.label);
      setCells(result.cells);
    };
    fetchData();
  }, []);

  useEffect(() => {
    if (!label?.days?.length || !label?.slots?.length || !cells?.length) return;

    const flatValues = cells.flat();
    const min = Math.min(...flatValues);
    const max = Math.max(...flatValues);
    const range = max - min;

    const roundedMin = niceRound(min);
    const roundedMax = niceRound(max);

    const getLevel = (value: number) => {
      if (range === 0) return 0;
      const step = range / 5;
      const level = Math.floor((value - min) / step);
      return Math.max(0, Math.min(4, level));
    };

    // 색상 단계 (밝은 파랑 → 진한 파랑)
    // const colorLevels = ['#F0F7FF', '#D6E8FF', '#A9D0FF', '#72B0FF', '#3A83E0'];

    const heatmapData: [number, number, number][] = [];
    for (let d = 0; d < label.days.length; d++) {
      for (let h = 0; h < label.slots.length; h++) {
        const value = cells[d][h];
        const level = getLevel(value);
        heatmapData.push([h, d, level]);
      }
    }

    const container = document.getElementById('weekly-usage-chart') as HTMLElement;
    if (!container) return;
    chartRef.current = Highcharts.chart({
      accessibility: {
        enabled: false,
      },
      chart: {
        renderTo: container,
        type: 'heatmap',
        backgroundColor: 'transparent',
        height: 420,
        spacing: [20, 10, 10, 10],
        style: { fontFamily: 'Pretendard, sans-serif' },
      },
      title: { text: '' },
      credits: { enabled: false },
      xAxis: {
        categories: label.slots,
        tickInterval: 3,
        labels: { style: { color: '#6B7280', fontSize: '14px' } },
      },
      yAxis: {
        categories: label.days,
        title: { text: '' },
        reversed: true,
        labels: {
          align: 'right',
          style: { color: '#6B7280', fontSize: '14px', fontWeight: '500' },
        },
      },
      colorAxis: {
        min: 0,
        max: 4,
        stops: [
          [0, '#F0F7FF'],
          [0.25, '#D6E8FF'],
          [0.5, '#A9D0FF'],
          [0.75, '#72B0FF'],
          [1, '#3A83E0'],
        ],
        labels: {
          style: {
            color: '#374151',
            fontSize: '12px',
            fontWeight: '600',
          },
          // 색상바 아래쪽 텍스트 (왼쪽/오른쪽 끝)
          formatter: function (this: Highcharts.AxisLabelsFormatterContextObject) {
            if (this.value === 0) return `${roundedMin}`;
            if (this.value === 4) return `${roundedMax}`;
            return '';
          },
        },
      },
      legend: {
        align: 'center',
        layout: 'horizontal',
        verticalAlign: 'bottom',
        symbolWidth: 300,
        symbolHeight: 10,
        margin: 20,
        padding: 10,
        title: {
          text: '사용량 (토큰 수)',
          style: {
            color: '#374151',
            fontSize: '12px',
            fontWeight: '600',
          },
        },
        itemStyle: {
          color: '#374151',
          fontSize: '12px',
          fontWeight: '600',
        },
      },
      tooltip: {
        backgroundColor: '#fff',
        borderColor: '#E5E7EB',
        borderRadius: 8,
        shadow: false,
        style: { color: '#111827', fontSize: '12px' },
        formatter: function (this: Highcharts.Point) {
          const xCategory = this.series.xAxis?.categories?.[this.x as number];
          const yCategory = this.series.yAxis?.categories?.[this.y as number];
          const rawValue = cells[this.y as number][this.x as number];
          return `<b>${yCategory}</b>요일 ${xCategory}<br/>사용량: <b>${rawValue}</b>`;
        } as Highcharts.TooltipFormatterCallbackFunction,
      },
      plotOptions: {
        heatmap: {
          borderWidth: 4,
          borderColor: '#fff',
          pointPadding: 0.3,
          dataLabels: { enabled: false },
          clip: false,
          crisp: false,
          borderRadius: 8 as unknown as number,
        },
      },
      series: [
        {
          name: '요일·시간별 사용량',
          data: heatmapData,
          type: 'heatmap',
        } as Highcharts.SeriesHeatmapOptions,
      ],
    });

    return () => chartRef.current?.destroy();
  }, [label, cells]);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="flex items-start gap-3">
        <FolderKanban size={20} className="text-red-500 mt-1" />
        <h3 className="text-xl font-semibold text-gray-900">시간대별 챗봇 사용량</h3>
      </div>
      <p className="mt-0.5 mb-4 text-sm text-gray-500">
        요일별 · 시간대별 사용량을 확인할 수 있습니다.
      </p>
      <div id="weekly-usage-chart" className="w-full" />
    </div>
  );
}
