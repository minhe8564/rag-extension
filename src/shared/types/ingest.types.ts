export interface IngestSummaryResult {
  total: number;
  completed: number;
  successCount: number;
  failedCount: number;
}

export interface IngestSummaryResponse {
  status: number;
  code: string;
  message: string;
  isSuccess: boolean;
  result: IngestSummaryResult;
}
