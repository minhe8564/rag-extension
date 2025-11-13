export function formatCreatedAt(value?: string) {
  if (!value) return '';
  try {
    const d = new Date(value);
    const y = d.getFullYear();
    const m = `${d.getMonth() + 1}`.padStart(2, '0');
    const day = `${d.getDate()}`.padStart(2, '0');
    const hh = `${d.getHours()}`.padStart(2, '0');
    const mm = `${d.getMinutes()}`.padStart(2, '0');
    return `${y}-${m}-${day} ${hh}:${mm}`;
  } catch {
    return value;
  }
}
