export type TotalUserType = {
  totalUser: number;
  asOf: string;
};

export type TotalDocsType = {
  totalDocs: number;
  asOf: string;
};

export type TotalErrorsType = {
  totalErrors: number;
  asOf: string;
};

export type ChangeTrend = {
  todayTotal: number;
  yesterdayTotal: number;
  deltaPct: number;
  direction: 'up' | 'down' | 'flat';
  asOf: string;
};

// 초기 실시간 데이터 타입
export type CurrentCount = {
  event: string;
  data: {
    accessUsers: number;
  };
};

export type TrendGroup = {
  user: ChangeTrend;
  document: ChangeTrend;
  error: ChangeTrend;
};

export type TotalGroup = {
  user: TotalUserType;
  document: TotalDocsType;
  error: TotalErrorsType;
};

export type CurrentGroup = {
  user: {
    event: string;
    data: { accessUsers: number };
  };
  document: {
    event: string;
    data: { accessUsers: number };
  };
  error: {
    event: string;
    data: { accessUsers: number };
  };
};

////////////////////////////
// 챗봇 사용량 시계열 조회
export type chatbotUsageTime = {
  timeframe: chatbotUsagetimeframe;
  items: Array<chatbotUsageItems>;
};
export type chatbotUsagetimeframe = {
  start: string;
  end: string;
  granularity: string;
};
export type chatbotUsageItems = {
  x: string;
  y: number;
};

////////////////////////////
// 모델별 평균 토큰, 응답 시간 타입
export type modelTokenTime = {
  timeframe: modelTimeFrame;
  models: Array<modelData>;
};

export type modelTimeFrame = {
  start: string;
  end: string;
  granularity: string;
};
export type modelData = {
  modelId: string;
  modelName: string;
  usageTokens: Array<modelTokenResponse>;
  averageResponseTimesMs: Array<modelTokenResponse>;
};
export type modelTokenResponse = {
  x: string;
  y: number;
};

////////////////////////////
// 시간대별 챗봇 사용량 히트맵 조회
export type chatbotUsageHeatmap = {
  timeframe: chatbotHeatmapTimeframe;
  label: chatbotHeatmapLabels;
  cells: Array<Array<number>>;
};
export type chatbotHeatmapTimeframe = {
  start: string;
  end: string;
};
export type chatbotHeatmapLabels = {
  days: Array<string>;
  slots: Array<string>;
};

////////////////////////////
// 자주 물어보는 키워드 조회
export type frequentKeywords = {
  timeframe: timeframeType;
  keywords: Array<keywordItem>;
};
export type timeframeType = {
  start: string;
  end: string;
};
export type keywordItem = {
  text: string;
  count: number;
  weight: number;
};

////////////////////////////
// 발생한 오류 목록 조회
export type errorList = {
  timeframe: errorTimeframe;
  errors: Array<errorItem>;
};
export type errorTimeframe = {
  start: string;
  end: string;
};
export type errorItem = {
  chatTitle: string;
  userType: string;
  userName: string;
  chatRoomId: string;
  errorType: string;
  occuredAt: string;
};

////////////////////////////
// 생성된 채팅방 목록 조회
export type createdChatrooms = {
  timeframe: chatroomTimeframe;
  chatrooms: Array<chatroomItem>;
};
export type chatroomTimeframe = {
  start: string;
  end: string;
};
export type chatroomItem = {
  title: string;
  userType: string;
  userName: string;
  chatRoomId: string;
  createdAt: string;
};
