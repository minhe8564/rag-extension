import { create } from 'zustand';

type ChatModelState = {
  selectedModel?: string;
  setSelectedModel: (m?: string) => void;
};

export const useChatModelStore = create<ChatModelState>((set) => ({
  selectedModel: undefined,
  setSelectedModel: (m) => set({ selectedModel: m }),
}));
