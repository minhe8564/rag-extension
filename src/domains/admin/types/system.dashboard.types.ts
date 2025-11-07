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
};

export type UseMonitoringStreamsOptions = {
  urls?: Streams;
  withCredentials?: boolean;
};

export type Errors = {
  cpu?: string | null;
  memory?: string | null;
  network?: string | null;
};

export type Connected = {
  cpu: boolean;
  memory: boolean;
  network: boolean;
};
