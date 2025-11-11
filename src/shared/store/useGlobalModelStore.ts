import { create } from 'zustand';

interface ModelState {
  model: string;
  setModel: (m: string) => void;
}

export const useGlobalModelStore = create<ModelState>((set) => ({
  model: localStorage.getItem('global-chat-model') ?? 'qwen3-v1:8b',
  setModel: (m) => {
    localStorage.setItem('global-chat-model', m);
    set({ model: m });
  },
}));
