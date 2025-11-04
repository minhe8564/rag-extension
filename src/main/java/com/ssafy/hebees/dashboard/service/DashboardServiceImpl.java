package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatbotTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.HeatmapLabel;
import com.ssafy.hebees.dashboard.dto.response.HeatmapResponse;
import com.ssafy.hebees.dashboard.dto.response.ModelSeries;
import com.ssafy.hebees.dashboard.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.dashboard.dto.response.TimeseriesPoint;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.entity.Granularity;
import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import com.ssafy.hebees.dashboard.entity.UsageAggregateHourly;
import com.ssafy.hebees.dashboard.repository.DocumentAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.ErrorAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.ModelAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UsageAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UserAggregateHourlyRepository;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.BiFunction;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DashboardServiceImpl implements DashboardService {

    private static final long HOURS_24 = 24L;

    private final UserAggregateHourlyRepository userAggregateHourlyRepository;
    private final DocumentAggregateHourlyRepository documentAggregateHourlyRepository;
    private final ErrorAggregateHourlyRepository errorAggregateHourlyRepository;
    private final UsageAggregateHourlyRepository usageAggregateHourlyRepository;
    private final ModelAggregateHourlyRepository modelAggregateHourlyRepository;

    @Override
    public Change24hResponse getAccessUsersChange24h() {
        return buildChange24hResponse(userAggregateHourlyRepository::sumAccessUserCountBetween);
    }

    @Override
    public Change24hResponse getUploadDocumentsChange24h() {
        return buildChange24hResponse(documentAggregateHourlyRepository::sumUploadCountBetween);
    }

    @Override
    public TotalDocumentsResponse getTotalUploadDocuments() {
        LocalDateTime asOf = LocalDateTime.now();
        int total = toInt(documentAggregateHourlyRepository.sumUploadCount());
        return TotalDocumentsResponse.of(total, asOf);
    }

    @Override
    public Change24hResponse getErrorsChange24h() {
        return buildChange24hResponse(errorAggregateHourlyRepository::sumTotalErrorCountBetween);
    }

    @Override
    public TotalErrorsResponse getTotalErrors() {
        LocalDateTime asOf = LocalDateTime.now();
        int total = toInt(errorAggregateHourlyRepository.sumTotalErrorCount());
        return TotalErrorsResponse.of(total, asOf);
    }

    @Override
    public ChatbotTimeSeriesResponse getChatbotTimeSeries(TimeSeriesRequest request) {
        TimeSeriesContext context = buildTimeSeriesContext(request);
        List<UsageAggregateHourly> aggregates = usageAggregateHourlyRepository.findBetween(
            context.startInclusive(), context.endExclusive());

        Map<LocalDate, Long> tokensByBucket = new HashMap<>();
        for (UsageAggregateHourly aggregate : aggregates) {
            if (aggregate.getAggregateDateTime() == null) {
                continue;
            }
            LocalDate bucket = resolveBucket(aggregate.getAggregateDateTime(),
                context.granularity());
            int tokens = aggregate.getTotalTokens() != null ? aggregate.getTotalTokens() : 0;
            tokensByBucket.merge(bucket, (long) tokens, Long::sum);
        }

        List<TimeseriesPoint> items = context.buckets().stream()
            .map(date -> new TimeseriesPoint(date, toInt(tokensByBucket.getOrDefault(date, 0L))))
            .toList();

        return new ChatbotTimeSeriesResponse(context.timeframe(), items);
    }

    @Override
    public ModelTimeSeriesResponse getModelTimeSeries(TimeSeriesRequest request) {
        TimeSeriesContext context = buildTimeSeriesContext(request);
        List<ModelAggregateHourly> aggregates = modelAggregateHourlyRepository.findBetween(
            context.startInclusive(), context.endExclusive());

        Map<UUID, Map<LocalDate, ModelBucketAccumulator>> modelMetrics = new HashMap<>();
        Map<UUID, String> modelNames = new HashMap<>();
        for (ModelAggregateHourly aggregate : aggregates) {
            LocalDate bucket = resolveBucket(aggregate.getAggregateDateTime(),
                context.granularity());
            Map<LocalDate, ModelBucketAccumulator> bucketMap =
                modelMetrics.computeIfAbsent(aggregate.getLlmNo(), key -> new HashMap<>());
            ModelBucketAccumulator accumulator =
                bucketMap.computeIfAbsent(bucket, key -> new ModelBucketAccumulator());
            accumulator.addTokens(aggregate.getTotalTokens());
            accumulator.addResponseTime(aggregate.getTotalResponseTimeMs(),
                aggregate.getResponseCount());
            if (aggregate.getLlmName() != null && !aggregate.getLlmName().isBlank()) {
                modelNames.putIfAbsent(aggregate.getLlmNo(), aggregate.getLlmName());
            }
        }

        List<UUID> sortedModelIds = modelMetrics.keySet().stream()
            .sorted(Comparator.comparing((UUID id) -> modelNames.getOrDefault(id, id.toString()))
                .thenComparing(UUID::toString))
            .toList();

        List<ModelSeries> series = new ArrayList<>();
        for (UUID modelId : sortedModelIds) {
            Map<LocalDate, ModelBucketAccumulator> bucketMap = modelMetrics.get(modelId);
            List<TimeseriesPoint> usagePoints = new ArrayList<>();
            List<TimeseriesPoint> responsePoints = new ArrayList<>();

            for (LocalDate bucket : context.buckets()) {
                ModelBucketAccumulator accumulator = bucketMap.get(bucket);
                int usage = accumulator != null ? accumulator.tokensAsInt() : 0;
                int average = accumulator != null ? accumulator.averageResponseTimeMs() : 0;
                usagePoints.add(new TimeseriesPoint(bucket, usage));
                responsePoints.add(new TimeseriesPoint(bucket, average));
            }

            String modelIdentifier = modelId.toString();
            String modelName = modelNames.getOrDefault(modelId, modelIdentifier);
            series.add(new ModelSeries(modelIdentifier, modelName, usagePoints, responsePoints));
        }

        return new ModelTimeSeriesResponse(context.timeframe(), series);
    }

    @Override
    public HeatmapResponse getChatbotHeatmap() {
        LocalDate today = LocalDate.now();
        LocalDate weekStart = today.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        LocalDate weekEnd = weekStart.plusDays(7);

        LocalDateTime startInclusive = weekStart.atStartOfDay();
        LocalDateTime endExclusive = weekEnd.atStartOfDay();

        List<UsageAggregateHourly> aggregates = usageAggregateHourlyRepository.findBetween(
            startInclusive, endExclusive);

        int[][] matrix = new int[7][24];

        for (UsageAggregateHourly aggregate : aggregates) {
            LocalDateTime timestamp = aggregate.getAggregateDateTime();
            if (timestamp == null || timestamp.isBefore(startInclusive)
                || !timestamp.isBefore(endExclusive)) {
                continue;
            }

            int dayIndex = dayOfWeekIndex(timestamp.getDayOfWeek());
            int hourIndex = timestamp.getHour();
            int tokens = aggregate.getTotalTokens() != null ? aggregate.getTotalTokens() : 0;

            long updated = (long) matrix[dayIndex][hourIndex] + tokens;
            matrix[dayIndex][hourIndex] = clampToInt(updated);
        }

        List<List<Integer>> cellRows = new ArrayList<>(7);
        for (int day = 0; day < 7; day++) {
            List<Integer> row = new ArrayList<>(24);
            for (int hour = 0; hour < 24; hour++) {
                row.add(matrix[day][hour]);
            }
            cellRows.add(List.copyOf(row));
        }

        Timeframe timeframe = new Timeframe(weekStart, weekEnd.minusDays(1),
            Granularity.week.name());
        return new HeatmapResponse(timeframe, HeatmapLabel.defaults(), List.copyOf(cellRows));
    }

    private Change24hResponse buildChange24hResponse(
        BiFunction<LocalDateTime, LocalDateTime, Long> sumBetween) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime referenceHour = now.truncatedTo(ChronoUnit.HOURS);

        LocalDateTime currentWindowStart = referenceHour.minusHours(HOURS_24);
        LocalDateTime previousWindowStart = currentWindowStart.minusHours(HOURS_24);

        int current = toInt(sumBetween.apply(currentWindowStart, referenceHour));
        int previous = toInt(sumBetween.apply(previousWindowStart, currentWindowStart));

        return toChange24hResponse(current, previous, now);
    }

    private TimeSeriesContext buildTimeSeriesContext(TimeSeriesRequest request) {
        Granularity granularity = request.granularity();
        int scale = request.scale();

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime referenceHour = now.truncatedTo(ChronoUnit.HOURS);
        List<LocalDate> buckets = new ArrayList<>(scale);

        switch (granularity) {
            case day -> {
                LocalDate startDate = referenceHour.toLocalDate().minusDays(scale - 1L);
                for (int i = 0; i < scale; i++) {
                    buckets.add(startDate.plusDays(i));
                }
            }
            case week -> {
                LocalDate currentWeekStart = referenceHour.toLocalDate()
                    .with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
                LocalDate startWeek = currentWeekStart.minusWeeks(scale - 1L);
                for (int i = 0; i < scale; i++) {
                    buckets.add(startWeek.plusWeeks(i));
                }
            }
            case month -> {
                LocalDate currentMonthStart = referenceHour.toLocalDate().withDayOfMonth(1);
                LocalDate startMonth = currentMonthStart.minusMonths(scale - 1L);
                for (int i = 0; i < scale; i++) {
                    buckets.add(startMonth.plusMonths(i));
                }
            }
            default ->
                throw new IllegalArgumentException("Unsupported granularity: " + granularity);
        }
        LocalDate firstBucket = buckets.get(0);
        LocalDate lastBucket = buckets.get(buckets.size() - 1);

        LocalDateTime startInclusive = firstBucket.atStartOfDay();
        LocalDateTime endExclusive = switch (granularity) {
            case day -> lastBucket.plusDays(1).atStartOfDay();
            case week -> lastBucket.plusWeeks(1).atStartOfDay();
            case month -> lastBucket.plusMonths(1).withDayOfMonth(1).atStartOfDay();
        };

        Timeframe timeframe = new Timeframe(firstBucket, lastBucket, granularity.name());

        return new TimeSeriesContext(startInclusive, endExclusive, List.copyOf(buckets), timeframe,
            granularity);
    }

    private LocalDate resolveBucket(LocalDateTime timestamp, Granularity granularity) {
        LocalDate date = timestamp.toLocalDate();
        return switch (granularity) {
            case day -> date;
            case week -> date.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
            case month -> date.withDayOfMonth(1);
        };
    }

    private int toInt(Long value) {
        if (value == null) {
            return 0;
        }
        return clampToInt(value.longValue());
    }

    private static int dayOfWeekIndex(DayOfWeek dayOfWeek) {
        return Math.floorMod(dayOfWeek.getValue() - DayOfWeek.MONDAY.getValue(), 7);
    }

    private static int clampToInt(long value) {
        if (value > Integer.MAX_VALUE) {
            return Integer.MAX_VALUE;
        }
        if (value < Integer.MIN_VALUE) {
            return Integer.MIN_VALUE;
        }
        return (int) value;
    }

    private static Change24hResponse toChange24hResponse(Integer todayTotal, Integer yesterdayTotal,
        LocalDateTime asOf) {
        double delta = yesterdayTotal != 0 ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Float.POSITIVE_INFINITY;

        return new Change24hResponse(
            todayTotal,
            yesterdayTotal,
            (float) delta,
            delta == 0 ? "flat" : (delta > 0 ? "up" : "down"),
            asOf
        );
    }

    private static class ModelBucketAccumulator {

        private long totalTokens;
        private double totalResponseTimeMs;
        private long responseCount;

        void addTokens(Integer tokens) {
            if (tokens != null) {
                totalTokens += tokens.longValue();
            }
        }

        void addResponseTime(Float responseTimeMs, Integer count) {
            if (responseTimeMs != null) {
                totalResponseTimeMs += responseTimeMs.doubleValue();
            }
            if (count != null) {
                responseCount += count.longValue();
            }
        }

        int tokensAsInt() {
            return DashboardServiceImpl.clampToInt(totalTokens);
        }

        int averageResponseTimeMs() {
            if (responseCount == 0) {
                return 0;
            }
            return (int) Math.round(totalResponseTimeMs / responseCount);
        }
    }

    private record TimeSeriesContext(
        LocalDateTime startInclusive,
        LocalDateTime endExclusive,
        List<LocalDate> buckets,
        Timeframe timeframe,
        Granularity granularity
    ) {

    }
}

