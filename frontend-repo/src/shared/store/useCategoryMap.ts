import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface CategoryState {
  categoryList: { id: string; name: string }[];
  categoryMap: Record<string, string>;
  setCategories: (list: { categoryNo: string; name: string }[]) => void;
}

export const useCategoryStore = create<CategoryState>()(
  persist(
    (set) => ({
      categoryList: [],
      categoryMap: {},

      setCategories: (list) => {
        const categoryList = list.map((c) => ({ id: c.categoryNo, name: c.name }));
        const categoryMap = Object.fromEntries(list.map((c) => [c.categoryNo, c.name]));

        set({ categoryList, categoryMap });
      },
    }),
    {
      name: 'category-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        categoryList: state.categoryList,
        categoryMap: state.categoryMap,
      }),
    }
  )
);
