import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type ReferencedDocsState = {
  open: boolean;
  hidden: boolean;
};

type ReferencedDocsStore = {
  // messageNo를 키로 하는 메시지별 상태
  docsStates: Record<string, ReferencedDocsState>;
  
  // 특정 메시지의 상태 가져오기
  getState: (messageNo: string) => ReferencedDocsState | null;
  
  // 특정 메시지의 상태 설정
  setState: (messageNo: string, state: Partial<ReferencedDocsState>) => void;
  
  // 특정 메시지의 상태 초기화
  resetState: (messageNo: string) => void;
};

export const useReferencedDocsStore = create<ReferencedDocsStore>()(
  persist(
    (set, get) => ({
      docsStates: {},
      
      getState: (messageNo: string) => {
        return get().docsStates[messageNo] || null;
      },
      
      setState: (messageNo: string, state: Partial<ReferencedDocsState>) => {
        set((prev) => ({
          docsStates: {
            ...prev.docsStates,
            [messageNo]: {
              open: prev.docsStates[messageNo]?.open ?? true,
              hidden: prev.docsStates[messageNo]?.hidden ?? false,
              ...state,
            },
          },
        }));
      },
      
      resetState: (messageNo: string) => {
        set((prev) => {
          const { [messageNo]: _, ...rest } = prev.docsStates;
          return { docsStates: rest };
        });
      },
    }),
    {
      name: 'referenced-docs-store',
      partialize: (state) => ({
        docsStates: state.docsStates,
      }),
    }
  )
);

