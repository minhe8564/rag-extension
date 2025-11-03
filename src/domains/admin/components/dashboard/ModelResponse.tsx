import { useEffect, useRef } from 'react';
import Highcharts from 'highcharts';

export default function ModelResponse() {
  const chartRef = useRef<Highcharts.Chart | null>(null);

  useEffect(() => {
    chartRef.current = Highcharts.chart('model-response-chart', {
      chart: {
        type: 'spline',
        animation: true,
        backgroundColor: '#fff',
        height: 300,
        style: { fontFamily: 'Pretendard, sans-serif' },
      },
      title: { text: '' },
      credits: { enabled: false },
      colors: ['var(--color-hebees)', 'var(--color-hebees-blue) ', 'var(--color-loading)'], // HEEBEES, BLUE, ORANGE

      xAxis: {
        type: 'datetime',
        tickPixelInterval: 150,
        lineColor: '#E5E7EB',
        gridLineColor: '#F3F4F6',
        labels: { style: { color: '#6B7280', fontSize: '11px' } },
      },
      yAxis: {
        title: { text: '응답 시간 (ms)', style: { color: '#6B7280', fontSize: '12px' } },
        gridLineDashStyle: 'Dash',
        gridLineColor: '#E5E7EB',
        labels: { style: { color: '#6B7280', fontSize: '11px' } },
        min: 0,
      },
      tooltip: {
        shared: true,
        backgroundColor: '#fff',
        borderColor: '#E5E7EB',
        borderRadius: 10,
        shadow: false,
        style: { color: '#111827', fontSize: '12px' },
        xDateFormat: '%H:%M:%S',
        pointFormat:
          "<b>{point.y}</b> ms<br/><span style='color:{series.color}'>●</span> {series.name}<br/>",
      },
      legend: {
        layout: 'horizontal',
        align: 'center',
        verticalAlign: 'bottom',
        itemStyle: { color: '#374151', fontSize: '12px' },
      },
      plotOptions: {
        spline: {
          lineWidth: 2,
          marker: { radius: 3, lineWidth: 1, lineColor: '#fff' },
          states: { hover: { lineWidth: 3 } },
          animation: { duration: 500 },
        },
      },
      series: [
        { name: 'claude-3-haiku', data: [], type: 'spline' },
        { name: 'gpt-4.1-mini', data: [], type: 'spline' },
        { name: 'gemini-1.5-pro', data: [], type: 'spline' },
      ],
    });

    // 🔹 실시간 더미 데이터 시뮬레이션
    const interval = setInterval(() => {
      const x = new Date().getTime();
      const responseData = [
        Math.floor(Math.random() * 250) + 100, // claude
        Math.floor(Math.random() * 180) + 80, // gpt
        Math.floor(Math.random() * 300) + 50, // gemini
      ];

      chartRef.current?.series.forEach((series, i) => {
        series.addPoint([x, responseData[i]], true, series.data.length > 20);
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="flex flex-col gap-2 my-3">
      <div className="flex flex-col w-full items-start justify-center p-4 border border-gray-200 rounded-xl bg-white">
        <h2 className="text-xl font-bold text-gray-800 mb-1">모델별 응답 시간</h2>
        <p className="text-xs text-gray-400">(claude, gpt, gemini 실시간 응답 속도)</p>
        <div
          id="model-response-chart"
          className="w-full border border-gray-200 rounded-xl p-2 bg-white shadow-sm"
        />
      </div>
    </section>
  );
}
