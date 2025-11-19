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

export type IngestNotifyMessage =
  | { completed: number }
  | {
      status?: number;
      result?: {
        total?: number;
        completed?: number;
        successCount?: number;
        failedCount?: number;
      };
    };
