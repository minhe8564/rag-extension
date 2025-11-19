import { create } from 'zustand';

interface IngestStreamState {
  enabled: boolean;
  setEnabled: (value: boolean) => void;
  reset: () => void;
}

export const useIngestStreamStore = create<IngestStreamState>((set) => ({
  enabled: false,
  setEnabled: (value) => set({ enabled: value }),
  reset: () => set({ enabled: false }),
}));
