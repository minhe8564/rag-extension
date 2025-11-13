export interface MyLlmKeyCreateRequest {
  llm: string;
  apiKey: string;
}

export interface MyLlmKeyResponse {
  llmKeyNo: string;
  userNo: string;
  strategyNo: string;
  llmName: string;
  llmNo: string;
  apiKey: string;
}

export interface MyLlmKeyListResponse {
  data: MyLlmKeyResponse[];
}
