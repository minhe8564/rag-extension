export type FileType = {
  name: string;
  size: number | null;
  category: string | null;
  collection: 'public' | 'hebees' | null;
  currentProgress: string | null;
  currentPercent: number | null;
  totalProgress: number | null;
};

export type CustomTooltipContext = {
  series: Highcharts.Series;
  point: { x: number; y: number; value: number };
};
