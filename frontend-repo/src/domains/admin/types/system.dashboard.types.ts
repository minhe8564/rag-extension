export type CpuEvent = {
  timestamp: string;
  cpuUsagePercent: number;
  totalCores: number;
  activeCores: number;
};

export type MemoryEvent = {
  timestamp: string;
  totalMemoryGB: number;
  usedMemoryGB: number;
  memoryUsagePercent: number;
};

export type NetworkEvent = {
  timestamp: string;
  inboundMbps: number;
  outboundMbps: number;
  bandwidthMbps: number;
};

export type Streams = {
  cpu?: string;
  memory?: string;
  network?: string;
  expense?: string;
};

export type UseMonitoringStreamsOptions = {
  urls?: Streams;
  withCredentials?: boolean;
};

export type Errors = {
  cpu?: string | null;
  memory?: string | null;
  network?: string | null;
  expense?: string | null;
};

export type Connected = {
  cpu?: boolean;
  memory?: boolean;
  network?: boolean;
  expense?: boolean;
};

export type ApiEnvelope<T> = {
  status: number;
  code: string;
  message: string;
  isSuccess: boolean;
  result: T;
};

export type ServiceName =
  | 'chunking-repo'
  | 'cross-encoder-repo'
  | 'embedding-repo'
  | 'extract-repo'
  | 'generation-repo'
  | 'ingest-repo'
  | 'python-backend-repo'
  | 'query-embedding-repo'
  | 'search-repo';

export type PerfLevel = 'NORMAL' | 'WARNING' | 'CRITICAL';

export type ServicePerformance = {
  serviceName: ServiceName;
  cpuUsagePercent: number;
  memoryUsagePercent: number;
  loadAvg1m: number;
  compositeScore: number;
  status: PerfLevel;
};

export type ServicesPerformanceResult = {
  timestamp: string;
  services: ServicePerformance[];
};

export type ServicesPerformanceResponse = ApiEnvelope<ServicesPerformanceResult>;

export type RuntimeStatus = 'RUNNING' | 'STOPPED' | 'UNKNOWN';

export type ServiceRuntimeStatus = {
  serviceName: ServiceName;
  status: RuntimeStatus;
  startedAt: string | null;
  uptimeSeconds: string;
};

export type ServicesStatusResult = {
  timestamp: string;
  services: ServiceRuntimeStatus[];
};

export type ServicesStatusResponse = ApiEnvelope<ServicesStatusResult>;

export type FileSystemUsage = {
  path: string;
  totalGB: number;
  usedGB: number;
  usagePercent: number;
};

export type StorageUsageResult = {
  timestamp: string;
  fileSystems: FileSystemUsage[];
};

export type StorageUsageResponse = ApiEnvelope<StorageUsageResult>;

export type ModelExpense = {
  model: string;
  inputPriceUsd: number;
  outputPriceUsd: number;
  totalPriceUsd: number;
};

export type ExpenseEvent = {
  timestamp: string;
  models: ModelExpense[];
  grandPriceUsd: number;
};

export type RagPipelineResponseTimeMetric = {
  name: string;
  averageTimeMs: number;
  count: number;
  minTimeMs: number;
  maxTimeMs: number;
};

export type RagPipelineResponseTimeResult = {
  metrics: RagPipelineResponseTimeMetric[];
};

export type RagPipelineResponseTimeResponse = ApiEnvelope<RagPipelineResponseTimeResult>;
