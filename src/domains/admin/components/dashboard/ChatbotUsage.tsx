import { useEffect, useRef } from 'react';
import Highcharts from 'highcharts';

export default function ChatbotUsage() {
  const chartRef = useRef<Highcharts.Chart | null>(null);

  useEffect(() => {
    chartRef.current = Highcharts.chart('chatbot-usage-chart', {
      chart: {
        type: 'areaspline', // 부드러운 영역형 꺾은선 그래프
        animation: true,
        backgroundColor: 'transparent',
        height: 300,
        style: {
          fontFamily: 'Pretendard, sans-serif',
        },
      },

      title: { text: '' },
      credits: { enabled: false },

      colors: ['var(--color-hebees)'],

      xAxis: {
        type: 'datetime',
        tickPixelInterval: 150,
        lineColor: '#E5E7EB',
        gridLineColor: '#F3F4F6',
        labels: {
          style: { color: '#6B7280', fontSize: '11px' },
        },
      },

      yAxis: {
        title: {
          text: '사용량 (토큰 수)',
          style: { color: '#6B7280', fontSize: '12px' },
        },
        labels: {
          style: { color: '#6B7280', fontSize: '11px' },
        },
        gridLineDashStyle: 'Dash',
        gridLineColor: '#E5E7EB',
        min: 0,
      },

      tooltip: {
        backgroundColor: '#ffffff',
        borderColor: '#E5E7EB',
        borderRadius: 10,
        borderWidth: 1,
        shadow: false,
        style: { color: '#111827', fontSize: '12px' },
        xDateFormat: '%H:%M:%S',
        pointFormat:
          '<b>{point.y}</b> 토큰<br/><span style="color:{series.color}">●</span> {series.name}',
      },

      legend: { enabled: false },

      plotOptions: {
        areaspline: {
          fillColor: {
            linearGradient: { x1: 0, y1: 0, x2: 0, y2: 300 },
            stops: [
              [0, 'rgba(var(--color-hebees-rgb), 0.7)'], // 더 연하게 (0.15)
              [1, 'rgba(var(--color-hebees-rgb), 0)'], // 완전 투명
            ],
          },
          lineWidth: 2,
          shadow: { color: 'rgba(0, 0, 0, 0.05)', width: 2, offsetX: 0, offsetY: 2 },
          marker: {
            radius: 4,
            fillColor: '#fff',
            lineColor: 'rgba(var(--color-hebees-rgb), 0.8)',
            lineWidth: 2,
          },
          states: {
            hover: {
              lineWidth: 3,
              halo: {
                size: 6,
                attributes: { opacity: 0.25 },
              },
            },
          },
          animation: { duration: 800 },
        },
      },

      series: [
        {
          type: 'areaspline',
          name: '챗봇 사용량',
          data: [],
          color: 'var(--color-hebees)',
        },
      ],
    });

    // 실시간 데이터 시뮬레이션
    const interval = setInterval(() => {
      const x = new Date().getTime();
      const y = Math.floor(Math.random() * 100) + 20;
      const chart = chartRef.current;
      if (chart && chart.series[0]) {
        chart.series[0].addPoint([x, y], true, chart.series[0].data.length > 20);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="flex flex-col gap-2 my-3">
      <div className="flex flex-col w-full items-start justify-center p-4 border border-gray-200 rounded-xl bg-white">
        <h2 className="text-xl font-bold text-gray-800 mb-1">챗봇 사용량</h2>
        <p className="text-xs text-gray-400">(일별, 주별, 월별) 사용량을 확인할 수 있습니다.</p>
        {/* 그래프 표시 영역 */}
        <div
          id="chatbot-usage-chart"
          className="w-full border border-gray-200 rounded-xl p-2 bg-white shadow-sm"
        />
      </div>
    </section>
  );
}
