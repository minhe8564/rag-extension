export type ApiEnvelope<T> = {
  status: number;
  code: string;
  message: string;
  isSuccess: boolean;
  result: T;
};

export type Pagination = {
  pageNum: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
};
