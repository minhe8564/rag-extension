import { useEffect, useRef } from 'react';
import Highcharts from 'highcharts';
import _Heatmap from 'highcharts/modules/heatmap';

export default function MonthlyUsage() {
  const chartRef = useRef<Highcharts.Chart | null>(null);

  useEffect(() => {
    const days = 30;
    const hours = 24;
    const hourLabels = Array.from({ length: 24 }, (_, i) => `${i}시`);

    const data: [number, number, number][] = [];
    for (let d = 0; d < days; d++) {
      for (let h = 0; h < hours; h++) {
        const usage = Math.floor(Math.random() * 100); // 0~100 랜덤
        data.push([d, h, usage]);
      }
    }

    // 차트 부분
    chartRef.current = Highcharts.chart('monthly-usage-chart', {
      chart: {
        type: 'heatmap',
        backgroundColor: 'transparent',
        height: 400,
        width: 760,
        style: { fontFamily: 'Pretendard, sans-serif' },
      },
      title: { text: '' },
      credits: { enabled: false },

      xAxis: {
        categories: Array.from({ length: days }, (_, i) => `${i}일`),
        labels: { style: { color: '#6B7280', fontSize: '10px' } },
        tickInterval: 1, // 1일 단위로 표시
      },
      yAxis: {
        categories: hourLabels, //  4시간 단위 시간대
        title: { text: '' },
        reversed: true,
        labels: { style: { color: '#6B7280', fontSize: '10px' } },
      },
      colorAxis: {
        min: 0,
        max: 100,
        stops: [
          [0, 'var(--color-retina-bg)'], // 가장 밝은색 (거의 없음)
          [0.33, '#8FB8D9'], // 약간 진함
          [0.66, '#3E7FB8'], // 중간
          [1, '#135D9C'], // 가장 진함 (#135D9C)
        ],
      },
      legend: {
        align: 'center',
        layout: 'horizontal',
        margin: 10,
        symbolWidth: 250,
        itemStyle: { color: '#374151', fontSize: '11px' },
      },
      tooltip: {
        hideDelay: 20,
        backgroundColor: '#fff',
        borderColor: '#E5E7EB',
        borderRadius: 8,
        shadow: false,
        style: { color: '#111827', fontSize: '12px' },
        formatter: function (this: Highcharts.Point) {
          const series = this.series as Highcharts.Series;
          const xCategory = series.xAxis?.categories?.[this.x as number];
          const yCategory = series.yAxis?.categories?.[this.y as number];
          return `
              <b>${xCategory}</b> / <b>${yCategory}</b><br/>
              사용량: <b>${this.y}</b>
            `;
        } as Highcharts.TooltipFormatterCallbackFunction,
      },
      series: [
        {
          name: '시간대별 챗봇 사용량',
          borderWidth: 1,
          borderColor: '#fff',
          data,
          dataLabels: { enabled: false },
          type: 'heatmap',
        },
      ],
    });

    return () => chartRef.current?.destroy();
  }, []);

  return (
    <section className="flex flex-col gap-2 my-3">
      <div className="flex flex-col w-full items-start justify-center p-4 border border-gray-200 rounded-xl bg-white">
        <h2 className="text-xl font-bold text-gray-800 mb-1">시간대별 챗봇 사용량</h2>
        <p className="text-xs text-gray-400">
          (일별, 주별, 월별) 사용량을 색의 진함으로 확인할 수 있습니다.
        </p>
        {/* Heatmap 영역 */}
        <div
          id="monthly-usage-chart"
          className="w-full border border-gray-200 rounded-xl p-2 bg-white shadow-sm"
        />
      </div>
    </section>
  );
}
