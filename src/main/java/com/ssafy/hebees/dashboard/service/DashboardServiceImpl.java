package com.ssafy.hebees.dashboard.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.chat.client.RunpodClient;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.chat.entity.MessageError;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.MessageErrorRepository;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.dashboard.dto.Granularity;
import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.dto.request.TrendKeywordCreateRequest;
import com.ssafy.hebees.dashboard.dto.request.TrendKeywordRequest;
import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatbotTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatroomsTodayResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatroomsTodayResponse.Chatroom;
import com.ssafy.hebees.dashboard.dto.response.ErrorsTodayResponse;
import com.ssafy.hebees.dashboard.dto.response.HeatmapLabel;
import com.ssafy.hebees.dashboard.dto.response.HeatmapResponse;
import com.ssafy.hebees.dashboard.dto.response.ModelSeries;
import com.ssafy.hebees.dashboard.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.dashboard.dto.response.TimeseriesPoint;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalUsersResponse;
import com.ssafy.hebees.dashboard.dto.response.TrendDirection;
import com.ssafy.hebees.dashboard.dto.response.TrendKeyword;
import com.ssafy.hebees.dashboard.dto.response.TrendKeywordCreateResponse;
import com.ssafy.hebees.dashboard.dto.response.TrendKeywordsResponse;
import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import com.ssafy.hebees.dashboard.entity.KeywordAggregateDaily;
import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import com.ssafy.hebees.dashboard.repository.DocumentAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.ErrorAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.KeywordAggregateDailyRepository;
import com.ssafy.hebees.dashboard.repository.ModelAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UsageAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UserAggregateHourlyRepository;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.function.BiFunction;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DashboardServiceImpl implements DashboardService {

    private static final long HOURS_24 = 24L;
    private static final int RECENT_CHATROOM_LIMIT = 10;
    private static final int RECENT_ERROR_LIMIT = 20;
    private static final String[] BUSINESS_TYPE_LABELS = {"개인 안경원", "체인 안경원", "제조 유통사"};

    private final UserAggregateHourlyRepository userAggregateHourlyRepository;
    private final DocumentAggregateHourlyRepository documentAggregateHourlyRepository;
    private final ErrorAggregateHourlyRepository errorAggregateHourlyRepository;
    private final UsageAggregateHourlyRepository usageAggregateHourlyRepository;
    private final ModelAggregateHourlyRepository modelAggregateHourlyRepository;
    private final KeywordAggregateDailyRepository keywordAggregateDailyRepository;
    private final SessionRepository sessionRepository;
    private final UserRepository userRepository;
    private final MessageErrorRepository messageErrorRepository;
    private final RunpodClient runpodClient;
    private final ObjectMapper objectMapper;

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
        long total = documentAggregateHourlyRepository.sumUploadCount();
        return TotalDocumentsResponse.of(total, asOf);
    }

    @Override
    public Change24hResponse getErrorsChange24h() {
        return buildChange24hResponse(errorAggregateHourlyRepository::sumTotalErrorCountBetween);
    }

    @Override
    public TotalErrorsResponse getTotalErrors() {
        LocalDateTime asOf = LocalDateTime.now();
        long total = errorAggregateHourlyRepository.sumTotalErrorCount();
        return TotalErrorsResponse.of(total, asOf);
    }

    @Override
    public TotalUsersResponse getTotalUsers() {
        LocalDateTime asOf = LocalDateTime.now();
        long total = userAggregateHourlyRepository.sumAccessUserCount();
        return TotalUsersResponse.of(total, asOf);
    }

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
            tokensByBucket.merge(bucket, tokens, Long::sum);
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
        LocalDate today = LocalDate.now(MonitoringUtils.KST);
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
    public TrendKeywordsResponse getTrendKeywords(TrendKeywordRequest request) {
        LocalDate end = LocalDate.now(MonitoringUtils.KST);
        LocalDate start = end.minusDays(request.scale() - 1);

        List<TrendKeyword> topKeywords = keywordAggregateDailyRepository.sumTopKeywords(start, end,
            request.topK());

        if (topKeywords.isEmpty()) {
            return new TrendKeywordsResponse(new Timeframe(start, end), List.of());
        }

        long min = topKeywords.stream().map(TrendKeyword::count).min(Long::compareTo).orElse(0L);
        long max = topKeywords.stream().map(TrendKeyword::count).max(Long::compareTo).orElse(0L);
        long diff = Math.max(1, max - min);

        List<TrendKeyword> normalized = topKeywords.stream()
            .map(keyword -> new TrendKeyword(keyword.text(), keyword.count(),
                (float) (keyword.count() - min) / diff))
            .toList();

        return new TrendKeywordsResponse(new Timeframe(start, end), normalized);
    }

    @Override
    public ChatroomsTodayResponse getChatroomsToday() {
        LocalDate today = LocalDate.now(MonitoringUtils.KST);
        LocalDateTime startInclusive = today.atStartOfDay();
        LocalDateTime endExclusive = startInclusive.plusDays(1);

        List<Session> sessions = sessionRepository.findCreatedBetween(startInclusive, endExclusive,
            RECENT_CHATROOM_LIMIT);

        if (sessions.isEmpty()) {
            return ChatroomsTodayResponse.empty(new Timeframe(today, today));
        }

        Set<UUID> userIds = sessions.stream()
            .map(Session::getUserNo)
            .filter(id -> id != null)
            .collect(Collectors.toSet());

        Map<UUID, User> usersById = userRepository.findAllById(userIds).stream()
            .collect(Collectors.toMap(User::getUuid, user -> user));

        List<Chatroom> chatrooms = sessions.stream()
            .sorted(Comparator.comparing(Session::getCreatedAt).reversed())
            .map(session -> {
                User owner = usersById.get(session.getUserNo());
                String userType = resolveUserType(owner);
                return new Chatroom(
                    session.getTitle(),
                    userType,
                    owner != null ? owner.getName() : "알 수 없음",
                    session.getSessionNo(),
                    session.getCreatedAt()
                );
            })
            .toList();

        return new ChatroomsTodayResponse(new Timeframe(today, today), chatrooms);
    }

    @Override
    public ErrorsTodayResponse getErrorsToday() {
        LocalDate today = LocalDate.now(MonitoringUtils.KST);
        LocalDateTime startInclusive = today.atStartOfDay();
        LocalDateTime endExclusive = startInclusive.plusDays(1);

        List<MessageError> errors = messageErrorRepository
            .findByCreatedAtBetweenOrderByCreatedAtDesc(startInclusive, endExclusive,
                PageRequest.of(0, RECENT_ERROR_LIMIT));

        if (errors.isEmpty()) {
            return new ErrorsTodayResponse(new Timeframe(today, today), List.of());
        }

        Set<UUID> sessionIds = errors.stream()
            .map(MessageError::getSessionNo)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        Map<UUID, Session> sessionsById = sessionRepository.findAllById(sessionIds).stream()
            .collect(Collectors.toMap(Session::getSessionNo, session -> session));

        Set<UUID> userIds = sessionsById.values().stream()
            .map(Session::getUserNo)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        Map<UUID, User> usersById = userRepository.findAllById(userIds).stream()
            .collect(Collectors.toMap(User::getUuid, user -> user));

        DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

        List<ErrorsTodayResponse.Error> errorItems = errors.stream()
            .map(error -> {
                Session session = sessionsById.get(error.getSessionNo());
                User owner = session != null ? usersById.get(session.getUserNo()) : null;

                String chatTitle = session != null ? session.getTitle() : "알 수 없음";
                String userType = resolveUserType(owner);
                String userName = owner != null ? owner.getName() : "알 수 없음";
                String chatRoomId = session != null ? session.getSessionNo().toString()
                    : error.getSessionNo() != null ? error.getSessionNo().toString() : null;
                String errorType = error.getType() != null ? error.getType().name() : "UNKNOWN";
                String occurredAt = error.getCreatedAt() != null
                    ? error.getCreatedAt().format(formatter)
                    : null;

                return new ErrorsTodayResponse.Error(chatTitle, userType, userName, chatRoomId,
                    errorType, occurredAt);
            })
            .toList();

        return new ErrorsTodayResponse(new Timeframe(today, today), errorItems);
    }

    @Override
    @Transactional
    public TrendKeywordCreateResponse recordTrendKeyword(TrendKeywordCreateRequest request) {
        String query = request.query();
        if (!StringUtils.hasText(query)) {
            return TrendKeywordCreateResponse.of(List.of());
        }

        LocalDate today = LocalDate.now(MonitoringUtils.KST);
        Set<String> extracted = extractKeywords(query);
        Set<String> normalizedKeywords = new LinkedHashSet<>();

        if (extracted.isEmpty()) {
            String fallback = normalizeKeyword(query);
            if (StringUtils.hasText(fallback)) {
                normalizedKeywords.add(fallback);
            }
        } else {
            for (String raw : extracted) {
                String keyword = normalizeKeyword(raw);
                if (StringUtils.hasText(keyword)) {
                    normalizedKeywords.add(keyword);
                }
            }
        }

        for (String keyword : normalizedKeywords) {
            keywordAggregateDailyRepository.findByAggregateDateAndKeyword(today, keyword)
                .ifPresentOrElse(
                    aggregate -> aggregate.increaseFrequency(1L),
                    () -> {
                        KeywordAggregateDaily created = KeywordAggregateDaily.builder()
                            .aggregateNo(UUID.randomUUID())
                            .aggregateDate(today)
                            .keyword(keyword)
                            .frequency(1L)
                            .build();
                        keywordAggregateDailyRepository.save(created);
                    }
                );
        }

        return TrendKeywordCreateResponse.of(List.copyOf(normalizedKeywords));
    }

    private Set<String> extractKeywords(String query) {
        try {
            RunpodChatResult result = runpodClient.chat(List.of(
                RunpodChatMessage.of("system",
                    "당신은 한국어 키워드 추출기입니다. 사용자의 문장을 읽고 핵심 키워드만 1~7개 사이로 JSON 배열 형식으로 반환하세요. 예: [\"키워드1\", \"키워드2\"]. 불필요한 설명은 넣지 마세요."),
                RunpodChatMessage.of("user", query)
            ));

            String content = result != null ? result.content() : null;
            return parseKeywordContent(content);
        } catch (Exception e) {
            log.warn("Runpod 키워드 추출 실패: {}", e.getMessage());
            return Set.of();
        }
    }

    private Set<String> parseKeywordContent(String content) {
        if (!StringUtils.hasText(content)) {
            return Set.of();
        }

        String trimmed = content.trim();
        try {
            JsonNode node = objectMapper.readTree(trimmed);
            if (node.isArray()) {
                Set<String> keywords = new LinkedHashSet<>();
                for (JsonNode element : node) {
                    if (element.isTextual()) {
                        String value = normalizeKeyword(element.asText());
                        if (StringUtils.hasText(value)) {
                            keywords.add(value);
                        }
                    }
                }
                return keywords;
            }
        } catch (Exception ignored) {
            // fall through to heuristic parsing
        }

        String normalized = trimmed.replaceAll("[\\[\\]\"']", "");
        Set<String> keywords = Arrays.stream(normalized.split("[\\n,]"))
            .map(this::normalizeKeyword)
            .filter(StringUtils::hasText)
            .collect(Collectors.toCollection(LinkedHashSet::new));

        return keywords;
    }

    private String normalizeKeyword(String keyword) {
        if (keyword == null) {
            return "";
        }
        String trimmed = keyword.trim().replaceAll("\\s{2,}", " ");
        if (trimmed.length() > 255) {
            return trimmed.substring(0, 255);
        }
        return trimmed;
    }

    private Change24hResponse buildChange24hResponse(
        BiFunction<LocalDateTime, LocalDateTime, Long> sumBetween) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime referenceHour = now.truncatedTo(ChronoUnit.HOURS);

        LocalDateTime currentWindowStart = referenceHour.minusHours(HOURS_24);
        LocalDateTime previousWindowStart = currentWindowStart.minusHours(HOURS_24);

        long current = sumBetween.apply(currentWindowStart, referenceHour);
        long previous = sumBetween.apply(previousWindowStart, currentWindowStart);

        return toChange24hResponse(current, previous, now);
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

    private int toInt(Long value) {
        if (value == null) {
            return 0;
        }
        return clampToInt(value);
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

    private static Change24hResponse toChange24hResponse(Long todayTotal, Long yesterdayTotal,
        LocalDateTime asOf) {
        double delta = yesterdayTotal != 0 ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Float.POSITIVE_INFINITY;

        return new Change24hResponse(
            todayTotal,
            yesterdayTotal,
            (float) delta,
            TrendDirection.of(delta),
            asOf
        );
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
            return DashboardServiceImpl.clampToInt(totalTokens);
        }

        int averageResponseTimeMs() {
            if (responseCount == 0) {
                return 0;
            }
            return (int) Math.round(totalResponseTimeMs / responseCount);
        }
    }

    private String resolveUserType(User user) {
        if (user == null) {
            return "알 수 없음";
        }

        int type = user.getBusinessType();
        if (type >= 0 && type < BUSINESS_TYPE_LABELS.length) {
            return BUSINESS_TYPE_LABELS[type];
        }
        return "기타";
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

