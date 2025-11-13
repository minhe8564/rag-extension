export interface MyLlmKeyCreateRequest {
  llm: string;
  apiKey: string;
}

export interface MyLlmKeyResponse {
  llmKeyNo: string;
  userNo: string;
  strategyNo: string;
  llmName: string;
  apiKey: string;
}

export interface MyLlmKeyListResponse {
  data: MyLlmKeyResponse[];
}
