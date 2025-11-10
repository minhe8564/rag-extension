import { create } from 'zustand';

interface ModelState {
  model: string;
  setModel: (m: string) => void;
}

export const useGlobalModelStore = create<ModelState>((set) => ({
  model: localStorage.getItem('global-chat-model') ?? 'gpt-4o',
  setModel: (m) => {
    localStorage.setItem('global-chat-model', m);
    set({ model: m });
  },
}));
