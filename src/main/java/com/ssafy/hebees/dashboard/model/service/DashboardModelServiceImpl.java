package com.ssafy.hebees.dashboard.model.service;

import com.ssafy.hebees.dashboard.dto.Granularity;
import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.model.dto.response.ChatbotTimeSeriesResponse;
import com.ssafy.hebees.dashboard.model.dto.response.HeatmapResponse.HeatmapLabel;
import com.ssafy.hebees.dashboard.model.dto.response.HeatmapResponse;
import com.ssafy.hebees.dashboard.model.dto.response.ModelTimeSeriesResponse.ModelSeries;
import com.ssafy.hebees.dashboard.model.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.dashboard.dto.response.TimeseriesPoint;
import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import com.ssafy.hebees.dashboard.model.repository.ModelAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.model.repository.UsageAggregateHourlyRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import com.ssafy.hebees.dashboard.dto.request.ModelExpenseUsageRequest;
import com.ssafy.hebees.dashboard.dto.response.ModelPriceResponse;
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
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DashboardModelServiceImpl implements DashboardModelService {

    private final UsageAggregateHourlyRepository usageAggregateHourlyRepository;
    private final ModelAggregateHourlyRepository modelAggregateHourlyRepository;
    private final StrategyRepository strategyRepository;
    private final ChatbotUsageStreamService chatbotUsageStreamService;
    private final AnalyticsExpenseStreamService analyticsExpenseStreamService;

    @Override
    public ChatbotTimeSeriesResponse getChatbotTimeSeries(TimeSeriesRequest request) {
        TimeSeriesContext context = buildTimeSeriesContext(request);
        List<ChatbotAggregateHourly> aggregates = usageAggregateHourlyRepository.findBetween(
            context.startInclusive(), context.endExclusive());

        Map<LocalDate, Long> tokensByBucket = new HashMap<>();
        for (ChatbotAggregateHourly aggregate : aggregates) {
            if (aggregate.getAggregateDateTime() == null) {
                continue;
            }
            LocalDate bucket = resolveBucket(aggregate.getAggregateDateTime(),
                context.granularity());
            Long tokens = aggregate.getTotalTokens() != null ? aggregate.getTotalTokens() : 0L;
            tokensByBucket.merge(bucket, tokens, (existing, value) -> existing + value);
        }

        List<TimeseriesPoint<Long>> items = context.buckets().stream()
            .map(date -> new TimeseriesPoint<>(date, tokensByBucket.getOrDefault(date, 0L)))
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
        }

        Set<UUID> llmNos = modelMetrics.keySet().stream()
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());
        if (!llmNos.isEmpty()) {
            strategyRepository.findAllById(llmNos)
                .forEach(strategy -> {
                    if (strategy == null || strategy.getStrategyNo() == null) {
                        return;
                    }
                    String candidate = strategy.getName();
                    if (!StringUtils.hasText(candidate)) {
                        candidate = strategy.getCode();
                    }
                    if (!StringUtils.hasText(candidate)) {
                        candidate = strategy.getStrategyNo().toString();
                    }
                    modelNames.put(strategy.getStrategyNo(), candidate);
                });
        }

        List<UUID> sortedModelIds = modelMetrics.keySet().stream()
            .sorted(Comparator.comparing((UUID id) -> modelNames.getOrDefault(id, id.toString()))
                .thenComparing(UUID::toString))
            .toList();

        List<ModelSeries> series = new ArrayList<>();
        for (UUID modelId : sortedModelIds) {
            Map<LocalDate, ModelBucketAccumulator> bucketMap = modelMetrics.get(modelId);
            List<TimeseriesPoint<Long>> usagePoints = new ArrayList<>();
            List<TimeseriesPoint<Long>> responsePoints = new ArrayList<>();

            for (LocalDate bucket : context.buckets()) {
                ModelBucketAccumulator accumulator = bucketMap.get(bucket);
                long usage = accumulator != null ? accumulator.tokensAsInt() : 0;
                long average = accumulator != null ? accumulator.averageResponseTimeMs() : 0;
                usagePoints.add(new TimeseriesPoint<>(bucket, usage));
                responsePoints.add(new TimeseriesPoint<>(bucket, average));
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

        List<ChatbotAggregateHourly> aggregates = usageAggregateHourlyRepository.findBetween(
            startInclusive, endExclusive);

        long[][] matrix = new long[7][24];

        for (ChatbotAggregateHourly aggregate : aggregates) {
            LocalDateTime timestamp = aggregate.getAggregateDateTime();
            if (timestamp == null || timestamp.isBefore(startInclusive)
                || !timestamp.isBefore(endExclusive)) {
                continue;
            }

            int dayIndex = dayOfWeekIndex(timestamp.getDayOfWeek());
            int hourIndex = timestamp.getHour();
            long tokens = aggregate.getTotalTokens() != null ? aggregate.getTotalTokens() : 0L;

            long updated = matrix[dayIndex][hourIndex] + tokens;
            matrix[dayIndex][hourIndex] = clampToInt(updated);
        }

        List<List<Long>> cellRows = new ArrayList<>(7);
        for (int day = 0; day < 7; day++) {
            List<Long> row = new ArrayList<>(24);
            for (int hour = 0; hour < 24; hour++) {
                row.add(matrix[day][hour]);
            }
            cellRows.add(List.copyOf(row));
        }

        Timeframe timeframe = new Timeframe(weekStart, weekEnd.minusDays(1),
            Granularity.WEEK.getValue());
        return new HeatmapResponse(timeframe, HeatmapLabel.defaults(), List.copyOf(cellRows));
    }

    @Override
    public SseEmitter subscribeChatbotStream(String lastEventId) {
        return chatbotUsageStreamService.subscribeChatbotStream(lastEventId);
    }

    @Override
    public SseEmitter subscribeExpenseStream(String lastEventId) {
        return analyticsExpenseStreamService.subscribeExpenseStream(lastEventId);
    }

    @Override
    @Transactional
    public void incrementChatbotRequests(long amount) {
        chatbotUsageStreamService.recordChatbotRequests(amount);
    }

    @Override
    @Transactional
    public ModelPriceResponse recordExpenseUsage(ModelExpenseUsageRequest request) {
        return analyticsExpenseStreamService.recordModelUsage(
            request.modelNo(), request.inputTokens(), request.outputTokens(),
            request.responseTimeMs());
    }

    private TimeSeriesContext buildTimeSeriesContext(TimeSeriesRequest request) {
        Granularity granularity = request.granularity();
        int scale = request.scale();

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime referenceHour = now.truncatedTo(ChronoUnit.HOURS);
        List<LocalDate> buckets = new ArrayList<>(scale);

        switch (granularity) {
            case DAY -> {
                LocalDate startDate = referenceHour.toLocalDate().minusDays(scale - 1L);
                for (int i = 0; i < scale; i++) {
                    buckets.add(startDate.plusDays(i));
                }
            }
            case WEEK -> {
                LocalDate currentWeekStart = referenceHour.toLocalDate()
                    .with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
                LocalDate startWeek = currentWeekStart.minusWeeks(scale - 1L);
                for (int i = 0; i < scale; i++) {
                    buckets.add(startWeek.plusWeeks(i));
                }
            }
            case MONTH -> {
                LocalDate currentMonthStart = referenceHour.toLocalDate().withDayOfMonth(1);
                LocalDate startMonth = currentMonthStart.minusMonths(scale - 1L);
                for (int i = 0; i < scale; i++) {
                    buckets.add(startMonth.plusMonths(i));
                }
            }
            default ->
                throw new IllegalArgumentException("Unsupported granularity: " + granularity);
        }
        LocalDate firstBucket = buckets.getFirst();
        LocalDate lastBucket = buckets.getLast();

        LocalDateTime startInclusive = firstBucket.atStartOfDay();
        LocalDateTime endExclusive = switch (granularity) {
            case DAY -> lastBucket.plusDays(1).atStartOfDay();
            case WEEK -> lastBucket.plusWeeks(1).atStartOfDay();
            case MONTH -> lastBucket.plusMonths(1).withDayOfMonth(1).atStartOfDay();
        };

        Timeframe timeframe = new Timeframe(firstBucket, lastBucket, granularity.getValue());

        return new TimeSeriesContext(startInclusive, endExclusive, List.copyOf(buckets), timeframe,
            granularity);
    }

    private LocalDate resolveBucket(LocalDateTime timestamp, Granularity granularity) {
        LocalDate date = timestamp.toLocalDate();
        return switch (granularity) {
            case DAY -> date;
            case WEEK -> date.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
            case MONTH -> date.withDayOfMonth(1);
        };
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

    private static class ModelBucketAccumulator {

        private long totalTokens;
        private double totalResponseTimeMs;
        private long responseCount;

        void addTokens(Long tokens) {
            if (tokens != null) {
                totalTokens += tokens;
            }
        }

        void addResponseTime(Float responseTimeMs, Long count) {
            if (responseTimeMs != null) {
                totalResponseTimeMs += responseTimeMs.doubleValue();
            }
            if (count != null) {
                responseCount += count;
            }
        }

        int tokensAsInt() {
            return DashboardModelServiceImpl.clampToInt(totalTokens);
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


