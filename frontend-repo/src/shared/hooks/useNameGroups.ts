import { useMemo } from 'react';
import type { UploadedDoc } from '@/shared/types/file.types';

export function useNameGroups(docs: UploadedDoc[]) {
  return useMemo(() => {
    const map = new Map<string, UploadedDoc[]>();

    docs.forEach((d) => {
      const key = `${d.name.toLowerCase()}|${d.categoryId ?? ''}`;
      const arr = map.get(key) ?? [];
      arr.push(d);
      map.set(key, arr);
    });

    const byRecent = (a: UploadedDoc, b: UploadedDoc) =>
      (new Date(b.createdAt || 0).getTime() || 0) - (new Date(a.createdAt || 0).getTime() || 0);

    map.forEach((arr) => arr.sort(byRecent));

    const conflicts = Array.from(map.values()).filter((arr) => arr.length > 1);

    const isLoser = (doc: UploadedDoc): boolean => {
      const key = `${doc.name.toLowerCase()}|${doc.categoryId ?? ''}`;
      const arr = map.get(key);
      return !!(arr && arr.length > 1 && arr[0].id !== doc.id);
    };

    return { map, conflicts, isLoser };
  }, [docs]);
}
