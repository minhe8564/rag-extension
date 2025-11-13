import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ChatModelState = {
  selectedModel?: string;
  selectedLlmNo?: string;
  setSelectedModel: (name?: string, llmNo?: string) => void;
};

export const useChatModelStore = create<ChatModelState>()(
  persist(
    (set) => ({
      selectedModel: undefined,
      selectedLlmNo: undefined,

      setSelectedModel: (name, llmNo) =>
        set({
          selectedModel: name,
          selectedLlmNo: llmNo,
        }),
    }),
    {
      name: 'chat-model-store',
      partialize: (state) => ({
        selectedModel: state.selectedModel,
        selectedLlmNo: state.selectedLlmNo,
      }),
    }
  )
);
