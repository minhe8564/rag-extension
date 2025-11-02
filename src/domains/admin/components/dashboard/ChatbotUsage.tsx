import { useEffect, useRef, useState } from 'react';
import Highcharts from 'highcharts';

export default function ChatbotUsage() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const periods = ['daily', 'weekly', 'monthly'] as const;
  const [period, setPeriod] = useState<(typeof periods)[number]>('daily');
  const [connection, setConnection] = useState<EventSource | ReturnType<typeof setInterval> | null>(
    null
  );

  // 주별 / 월별 더미 데이터
  // const staticData = {
  //   weekly: Array.from({ length: 8 }, (_, i) => ({
  //     x: Date.UTC(2025, 10, 2 - i * 7),
  //     y: Math.floor(Math.random() * 700),
  //   })),
  //   monthly: Array.from({ length: 6 }, (_, i) => ({
  //     x: Date.UTC(2025, 10 - i, 1),
  //     y: Math.floor(Math.random() * 3000),
  //   })),
  // };

  // 차트 부분
  useEffect(() => {
    chartRef.current = Highcharts.chart('chatbot-usage-chart', {
      chart: {
        type: 'areaspline',
        backgroundColor: 'transparent',
        height: 300,
        animation: true,
      },
      title: { text: '' },
      credits: { enabled: false },
      xAxis: {
        type: 'datetime',
        tickPixelInterval: 150,
        labels: { style: { fontSize: '11px', color: '#6B7280' } },
      },
      yAxis: {
        title: { text: '사용량 (토큰 수)' },
        min: 0,
      },
      tooltip: {
        xDateFormat: '%H:%M:%S',
        pointFormat: '<b>{point.y}</b> 토큰',
      },
      series: [
        {
          type: 'areaspline',
          name: '챗봇 사용량',
          color: 'var(--color-hebees)',
          data: [],
        },
      ],
    });
  }, []);

  // 기간 변경 핸들러
  const handlePeriodChange = (type: (typeof periods)[number]) => {
    setPeriod(type);

    const chart = chartRef.current;
    if (!chart) return;

    // 통계 기간에 따른 x,t축 변경
    if (type === 'daily') {
      chart.xAxis[0].update({
        tickInterval: 3600 * 1000, // 1시간 간격 (24시간)
        labels: { format: '{value:%H:%M}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.update({
        tooltip: { xDateFormat: '%H:%M', pointFormat: '<b>{point.y}</b> 토큰' },
        yAxis: { title: { text: '시간당 사용량 (토큰)' } },
      });
    } else if (type === 'weekly') {
      chart.xAxis[0].update({
        tickInterval: 24 * 3600 * 1000, // 하루 간격 (7일)
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.update({
        tooltip: { xDateFormat: '%m/%d', pointFormat: '<b>{point.y}</b> 토큰' },
        yAxis: { title: { text: '일별 총 사용량 (토큰)' } },
      });
    } else if (type === 'monthly') {
      chart.xAxis[0].update({
        tickInterval: 7 * 24 * 3600 * 1000, // 1주 간격 (5주)
        labels: { format: '{value:%m/%d}', style: { fontSize: '11px', color: '#6B7280' } },
      });
      chart.update({
        tooltip: { xDateFormat: '%m/%d', pointFormat: '<b>{point.y}</b> 토큰' },
        yAxis: { title: { text: '주별 총 사용량 (토큰)' } },
      });
    }

    // 실시간 interval 정리
    // if (intervalId instanceof EventSource) intervalId.close();
    // else if (intervalId) clearInterval(intervalId);

    // 일별
    if (type === 'daily') {
      const eventSource = new EventSource('');
      setConnection(eventSource);

      eventSource.onmessage = (event) => {
        try {
          const { timestamp, value } = JSON.parse(event.data);
          chart.series[0].addPoint([timestamp, value], true, chart.series[0].data.length > 50);
        } catch (error) {
          console.error('챗봇 사용량 데이터 파싱 오류:', error);
        }
      };

      eventSource.onerror = (err) => {
        console.error('챗봇 사용량 데이터 수신 오류: SSE 연결도 끄겠음', err);
        eventSource.close();
        setConnection(null);
      };
    } else {
      fetch(``)
        .then((res) => res.json())
        .then((data) => {
          // [{ timestamp, value }] 형태라고 가정
          chart.series[0].setData(
            data.map((d: { timestamp: number; value: number }) => [d.timestamp, d.value]),
            true
          );
        })
        .catch((err) => console.error(`${type} 데이터 불러오기 오류:`, err));
    }
  };

  // 초기 상태 일별 시작
  useEffect(() => {
    handlePeriodChange('daily');
    return () => {
      // if (intervalId instanceof EventSource) intervalId.close();
      // else if (intervalId) clearInterval(intervalId);
    };
  }, []);

  return (
    <section className="flex flex-col gap-2 my-3">
      <div className="flex flex-col w-full p-4 border border-gray-200 rounded-xl bg-white">
        <h2 className="text-xl font-bold text-gray-800 mb-2">챗봇 사용량</h2>

        {/* 기간 전환 버튼 */}
        <div className="flex gap-2 mb-3">
          {['daily', 'weekly', 'monthly'].map((p) => (
            <button
              key={p}
              onClick={() => handlePeriodChange(p as (typeof periods)[number])}
              className={`px-3 py-1 text-sm rounded-lg transition ${
                period === p
                  ? 'bg-[var(--color-hebees)] text-white'
                  : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
              }`}
            >
              {p === 'daily' ? '일별' : p === 'weekly' ? '주별' : '월별'}
            </button>
          ))}
        </div>

        <div
          id="chatbot-usage-chart"
          className="w-full border border-gray-200 rounded-xl p-2 bg-white shadow-sm"
        />
      </div>
    </section>
  );
}
