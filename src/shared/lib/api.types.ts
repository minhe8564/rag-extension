export type ApiEnvelope<T> = {
  status: number;
  code: string;
  message: string;
  isSuccess: boolean;
  result: T;
};
