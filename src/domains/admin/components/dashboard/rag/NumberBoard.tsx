import { useState, useEffect } from 'react';
import { Users, FileText, TriangleAlert, TrendingUp, TrendingDown } from 'lucide-react';
import Card from '@/shared/components/Card';
import { EventSourcePolyfill } from 'event-source-polyfill';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import {
  getTotalUserCount,
  getUserChangeTrend,
  getTotalDocumentCount,
  getDocumentChangeTrend,
  getTotalErrorCount,
  getErrorChangeTrend,
} from '@/domains/admin/api/rag.dashboard.api';
import type {
  TrendGroup,
  TotalGroup,
  CurrentGroup,
} from '@/domains/admin/types/rag.dashboard.types';

export default function NumberBoard() {
  // 실시간 데이터
  const [currentData, setCurrentData] = useState<CurrentGroup | null>(null);
  // 토탈 데이터
  const [totalData, setTotalData] = useState<TotalGroup | null>(null);
  // 증감률
  const [trendData, setTrendData] = useState<TrendGroup | null>(null);

  const SPRING_API_BASE_URL = import.meta.env.VITE_SPRING_BASE_URL;

  const token = useAuthStore((state) => state.accessToken);
  // 실시간 데이터 로딩
  useEffect(() => {
    const sources = {
      user: new EventSourcePolyfill(
        `${SPRING_API_BASE_URL}/api/v1/analytics/metrics/access-users/stream`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      ),
      document: new EventSourcePolyfill(
        `${SPRING_API_BASE_URL}/api/v1/analytics/metrics/upload-documents/stream`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      ),
      error: new EventSourcePolyfill(
        `${SPRING_API_BASE_URL}/api/v1/analytics/metrics/errors/stream`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      ),
    };

    //  key에 따른 데이터 필드 매핑
    const fieldMap = {
      user: 'accessUsers',
      document: 'uploadedDocs',
      error: 'errorCount',
    } as const;

    // 공통 이벤트 핸들러
    const handleEvent = (key: keyof typeof sources) => (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data);
        console.log(`📡 ${key} ${event.type} 이벤트 수신`, parsed);

        setCurrentData((prev) => {
          const base = prev ?? {
            user: { event: '', data: { accessUsers: 0 } },
            document: { event: '', data: { accessUsers: 0 } },
            error: { event: '', data: { accessUsers: 0 } },
          };

          // 해당 key에 맞는 필드명 가져오기
          const field = fieldMap[key];
          const newValue = parsed[field] ?? base[key].data.accessUsers;

          return {
            ...base,
            [key]: {
              event: event.type, // 'init' | 'update'
              data: { accessUsers: newValue },
            },
          };
        });
      } catch (err) {
        console.error(`❌ ${key} 이벤트 파싱 실패:`, err);
      }
    };

    // 모든 소스에 대해 init/update 이벤트 리스너 등록
    (Object.keys(sources) as (keyof typeof sources)[]).forEach((key) => {
      const source = sources[key] as EventSource;
      const listener = handleEvent(key);
      source.addEventListener('init', listener);
      source.addEventListener('update', listener);

      // 연결 성공 로그
      source.onopen = () => console.log(`✅ ${key} SSE 연결 성공`);
      // 에러 로그
      source.onerror = (err) => console.error(`🔴 ${key} SSE 연결 에러`, err);
    });

    // 컴포넌트 unmount 시 연결 종료
    return () => {
      Object.values(sources).forEach((s) => s.close());
      console.log(' SSE 연결 종료');
    };
  }, []);

  //  나머지 데이터 로딩
  useEffect(() => {
    const fetchTotalData = async () => {
      const [totalUserData, totalDocumentData, totalErrorData] = await Promise.all([
        getTotalUserCount(),
        getTotalDocumentCount(),
        getTotalErrorCount(),
      ]);

      const normalziedTotalUserData = {
        user: { totalUser: totalUserData.totalUser, asOf: totalUserData.asOf },
        document: { totalDocs: totalDocumentData.totalDocs, asOf: totalDocumentData.asOf },
        error: { totalErrors: totalErrorData.totalErrors, asOf: totalErrorData.asOf },
      };
      setTotalData(normalziedTotalUserData);
    };

    const fetchTrendData = async () => {
      const [trendUserData, trendDocumentData, trendErrorData] = await Promise.all([
        getUserChangeTrend(),
        getDocumentChangeTrend(),
        getErrorChangeTrend(),
      ]);
      const normalziedTrendUserData = {
        user: {
          todayTotal: trendUserData.todayTotal,
          yesterdayTotal: trendUserData.yesterdayTotal,
          deltaPct: trendUserData.deltaPct,
          direction: trendUserData.direction,
          asOf: trendUserData.asOf,
        },
        document: {
          todayTotal: trendDocumentData.todayTotal,
          yesterdayTotal: trendDocumentData.yesterdayTotal,
          deltaPct: trendDocumentData.deltaPct,
          direction: trendDocumentData.direction,
          asOf: trendDocumentData.asOf,
        },
        error: {
          todayTotal: trendErrorData.todayTotal,
          yesterdayTotal: trendErrorData.yesterdayTotal,
          deltaPct: trendErrorData.deltaPct,
          direction: trendErrorData.direction,
          asOf: trendErrorData.asOf,
        },
      };
      setTrendData(normalziedTrendUserData);
    };

    fetchTrendData();
    fetchTotalData();
  }, []);

  const totalFieldMap = {
    user: 'totalUser',
    document: 'totalDocs',
    error: 'totalErrors',
  } as const;

  const renderCard = (
    key: keyof TrendGroup,
    title: string,
    icon: JSX.Element,
    totalLabel: string
  ) => {
    const current = currentData?.[key]?.data.accessUsers ?? 0;
    const trend = trendData?.[key];
    const total = totalData?.[key];
    // TOTAL 수는 API에서 가져온 데이터 사용
    const field = totalFieldMap[key];
    const totalCount = (total as Record<string, number | string | undefined>)?.[field] ?? 0;
    // 하루 전 대비 수는 API에서 가져온 데이터로 계산
    const deltaValue =
      trend?.deltaPct !== undefined ? Number((trend.deltaPct * 100).toFixed(2)) : 0;
    const direction = trend?.direction ?? 'flat';

    const IconArrow = direction === 'up' ? TrendingUp : direction === 'down' ? TrendingDown : null;
    const sign = deltaValue > 0 ? '+' : '';
    const color =
      direction === 'up'
        ? 'text-green-600'
        : direction === 'down'
          ? 'text-red-600'
          : 'text-gray-500';

    return (
      <div className="p-4 sm:p-5 h-full flex flex-col bg-white rounded-lg border shadow-sm">
        {/* 헤더 */}
        <div className="mb-4 flex items-center gap-2">
          {icon}
          <span className="text-xl font-bold text-gray-900">{title}</span>
        </div>

        {/* 메인 숫자 */}
        <div className="flex flex-col space-y-1 justify-center flex-1">
          <div className="flex items-center gap-0.5">
            <div className="relative aspect-square w-[45%] flex items-center justify-center overflow-hidden">
              <p className="absolute left-0 right-0 text-4xl sm:text-4xl font-extrabold text-gray-900">
                {current.toLocaleString()}
              </p>
            </div>
            <span className="text-xl text-gray-400 mx-[2px] mt-2.5">/</span>
            <span className="text-xl text-gray-400 font-normal mt-2.5">
              {totalLabel} {totalCount.toLocaleString()}
            </span>
          </div>

          <div className="flex items-center">
            <div className="flex items-center gap-1.5 border rounded-lg px-2 py-1 shadow-sm bg-white">
              {IconArrow && (
                <IconArrow
                  size={11}
                  className={`${
                    direction === 'up'
                      ? 'text-green-600'
                      : direction === 'down'
                        ? 'text-red-600'
                        : 'text-gray-400'
                  }`}
                />
              )}
              <span className="text-gray-600 text-lg">하루 전 대비</span>
              <span className={`text-lg font-semibold ${color}`}>
                {sign}
                {Math.abs(deltaValue).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card
      title="오늘의 실시간 로그"
      subtitle="실시간으로 처리되는 로그 데이터"
      className="p-4 h-full flex flex-col"
    >
      <div className="mb-4 flex items-center"></div>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-2 flex-1">
        {renderCard(
          'user',
          '현재 사용자 수',
          <div className="h-[3rem] w-[3rem] rounded-lg bg-[var(--color-hebees-blue-bg)] flex items-center justify-center shadow-sm">
            <Users size={35} className="text-[var(--color-hebees-blue)]" />
          </div>,
          '총'
        )}
        {renderCard(
          'document',
          '업로드 문서 수',
          <div className="h-[3rem] w-[3rem] rounded-lg bg-[var(--color-hebees-bg)] flex items-center justify-center shadow-sm">
            <FileText size={35} className="text-[var(--color-hebees)]" />
          </div>,
          '총'
        )}
        {renderCard(
          'error',
          '오류 발생 수',
          <div className="h-[3rem] w-[3rem] rounded-lg bg-red-50 flex items-center justify-center shadow-sm">
            <TriangleAlert size={35} className="text-red-500" />
          </div>,
          '총'
        )}
      </section>
    </Card>
  );
}
