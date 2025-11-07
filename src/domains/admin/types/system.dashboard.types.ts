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
