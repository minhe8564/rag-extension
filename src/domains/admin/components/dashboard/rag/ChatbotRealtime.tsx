import { useEffect, useRef } from 'react';
import Highcharts from 'highcharts';
import { MessageSquare } from 'lucide-react';
import type { initData, updateData } from '@/domains/admin/types/rag.dashboard.types';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/domains/auth/store/auth.store';

export default function ChatbotUsageRealtime() {
  const chartRef = useRef<Highcharts.Chart | null>(null);
  const SPRING_API_BASE_URL = import.meta.env.VITE_SPRING_BASE_URL;
  const token = useAuthStore((state) => state.accessToken);

  // 차트 초기화
  useEffect(() => {
    chartRef.current = Highcharts.chart('chatbot-usage-container', {
      accessibility: {
        enabled: false,
      },
      chart: {
        type: 'areaspline',
        backgroundColor: 'transparent',
        animation: true,
        marginRight: 10,
        height: 320,
      },

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
          data: [],
        },
      ],
    });

    return () => chartRef.current?.destroy();
  }, []);

  useEffect(() => {
    const sources = {
      realtimeUsage: new EventSourcePolyfill(
        `${SPRING_API_BASE_URL}/api/v1/analytics/metrics/chatbot/stream`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      ),
    };

    sources.realtimeUsage.addEventListener('init', (event) => {
      const e = event as MessageEvent;
      const InitData = JSON.parse(e.data) as initData;
      console.log('🔥 SSE onmessage PARSED:', InitData);
      const initTime = new Date(InitData.timestamp).getTime();
      const initRequestCount = InitData.requestCount;

      const chart = chartRef.current;
      if (chart) {
        const series = chart.series[0];
        series.setData([[initTime, initRequestCount]], true);
      }
    });

    sources.realtimeUsage.addEventListener('update', (event) => {
      const e = event as MessageEvent;
      const LiveData = JSON.parse(e.data) as updateData;
      console.log('🔥 SSE onmessage PARSED (live):', LiveData);
      const updateTime = new Date(LiveData.timestamp).getTime();
      const updateRequestCount = LiveData.requestCount;

      const chart = chartRef.current;
      const series = chart?.series[0];
      series?.addPoint([updateTime, updateRequestCount], true, series.data.length >= 6);
    });

    return () => {
      sources.realtimeUsage.close();
    };
  }, [token]);

  return (
    <div className="flex h-full flex-col rounded-2xl border bg-white p-8 shadow-sm">
      <div className="flex items-start gap-3">
        <MessageSquare size={18} className="text-blue-500 mt-1" />
        <h3 className="text-xl font-semibold text-gray-900">실시간 챗봇 사용량</h3>
      </div>
      <p className="mt-0.5 mb-12 text-sm text-gray-500">10초 단위 업데이트</p>
      <div id="chatbot-usage-container" className="w-full" />
    </div>
  );
}
