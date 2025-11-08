import { useEffect, useRef } from 'react';
import Highcharts from 'highcharts';
import Card from '@/shared/components/Card';

export default function ChatbotUsageRealtime() {
  const chartRef = useRef<Highcharts.Chart | null>(null);

  useEffect(() => {
    // 초기 데이터 (더미)
    const initialData = Array.from({ length: 10 }, (_, i) => ({
      x: Date.now() - (10 - i) * 10000,
      y: Math.floor(Math.random() * 60) + 20,
    }));

    // 차트 생성
    chartRef.current = Highcharts.chart('chatbot-usage-container', {
      chart: {
        type: 'areaspline',
        backgroundColor: 'transparent',
        animation: true,
        marginRight: 10,
        height: 320,
      },
      // 🔹 내부 title / subtitle 제거
      title: { text: undefined },
      subtitle: { text: undefined },

      xAxis: {
        type: 'datetime',
        tickPixelInterval: 150,
        labels: { style: { color: '#6B7280' } },
      },
      yAxis: {
        title: { text: '' },
        labels: { style: { color: '#6B7280' } },
        gridLineColor: '#E5E7EB',
        min: 0,
      },
      legend: { enabled: false },
      tooltip: {
        xDateFormat: '%p %I:%M:%S',
        pointFormat: '<b>{point.y}</b> 요청',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderColor: '#E5E7EB',
      },
      plotOptions: {
        areaspline: {
          color: '#81BAFF',
          fillOpacity: 0.3,
          lineWidth: 2,
          marker: { enabled: false },
        },
      },
      credits: { enabled: false },
      series: [
        {
          name: '요청 수',
          type: 'areaspline',
          data: initialData,
        },
      ],
    });

    // 10초마다 데이터 갱신
    const interval = setInterval(() => {
      const chart = chartRef.current;
      if (!chart) return;

      // 🔹 실제 API 연결 시 아래 부분 교체
      const timestamp = Date.now();
      const requestCount = Math.floor(Math.random() * 60) + 20;

      const series = chart.series[0];
      series.addPoint([timestamp, requestCount], true, series.data.length >= 10);
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Card title="실시간 챗봇 사용량" subtitle="10초 단위 업데이트" className="p-4">
      <div id="chatbot-usage-container" className="w-full" />
    </Card>
  );
}
