package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.response.AccessUserEvent;
import com.ssafy.hebees.dashboard.dto.response.ErrorEvent;
import com.ssafy.hebees.dashboard.dto.response.TrendDirection;
import com.ssafy.hebees.dashboard.dto.response.UploadDocumentEvent;
import com.ssafy.hebees.dashboard.entity.DocumentAggregateHourly;
import com.ssafy.hebees.dashboard.entity.ErrorAggregateHourly;
import com.ssafy.hebees.dashboard.entity.UserAggregateHourly;
import com.ssafy.hebees.dashboard.repository.DocumentAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.ErrorAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UserAggregateHourlyRepository;
import com.ssafy.hebees.common.util.MonitoringUtils;
import jakarta.annotation.PostConstruct;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.EnumMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Service
@RequiredArgsConstructor
public class DashboardMetricStreamServiceImpl implements DashboardMetricStreamService {

    private final UserAggregateHourlyRepository userAggregateHourlyRepository;
    private final DocumentAggregateHourlyRepository documentAggregateHourlyRepository;
    private final ErrorAggregateHourlyRepository errorAggregateHourlyRepository;
    private final DashboardService dashboardService;

    private final Map<MetricType, Set<SseEmitter>> emitters =
        new EnumMap<>(MetricType.class);

    @PostConstruct
    void initialize() {
        for (MetricType type : MetricType.values()) {
            emitters.put(type, new CopyOnWriteArraySet<>());
        }
    }

    @Override
    public SseEmitter subscribeAccessUsers(String lastEventId) {
        return subscribe(MetricType.ACCESS_USERS, lastEventId);
    }

    @Override
    public SseEmitter subscribeUploadDocuments(String lastEventId) {
        return subscribe(MetricType.UPLOAD_DOCUMENTS, lastEventId);
    }

    @Override
    public SseEmitter subscribeErrors(String lastEventId) {
        return subscribe(MetricType.ERRORS, lastEventId);
    }

    @Override
    @Transactional
    public long incrementCurrentAccessUsers(long delta) {
        LocalDateTime bucket = currentHour();
        UserAggregateHourly aggregate = userAggregateHourlyRepository.findById(bucket)
            .orElseGet(() -> UserAggregateHourly.builder()
                .aggregateDatetime(bucket)
                .build());

        long updatedValue = aggregate.increaseAccessUserCount(delta);
        userAggregateHourlyRepository.save(aggregate);
        long todayTotal = fetchMetricValue(MetricType.ACCESS_USERS);
        broadcastUpdate(MetricType.ACCESS_USERS, todayTotal);
        return todayTotal;
    }

    @Override
    @Transactional
    public long incrementCurrentUploadDocuments(long delta) {
        LocalDateTime bucket = currentHour();
        DocumentAggregateHourly aggregate = documentAggregateHourlyRepository.findById(bucket)
            .orElseGet(() -> DocumentAggregateHourly.builder()
                .aggregateDatetime(bucket)
                .build());

        long updatedValue = aggregate.increaseUploadCount(delta);
        documentAggregateHourlyRepository.save(aggregate);
        long todayTotal = fetchMetricValue(MetricType.UPLOAD_DOCUMENTS);
        broadcastUpdate(MetricType.UPLOAD_DOCUMENTS, todayTotal);
        return todayTotal;
    }

    @Override
    @Transactional
    public long incrementCurrentErrors(long systemDelta, long responseDelta) {
        LocalDateTime bucket = currentHour();
        ErrorAggregateHourly aggregate = errorAggregateHourlyRepository.findById(bucket)
            .orElseGet(() -> ErrorAggregateHourly.builder()
                .errorAggregateDatetime(bucket)
                .build());

        long updatedValue = aggregate.increaseErrorCounts(systemDelta, responseDelta);
        errorAggregateHourlyRepository.save(aggregate);
        long todayTotal = fetchMetricValue(MetricType.ERRORS);
        broadcastUpdate(MetricType.ERRORS, todayTotal);
        return todayTotal;
    }

    private SseEmitter subscribe(MetricType type, String lastEventId) {
        SseEmitter emitter = new SseEmitter(0L);
        emitters.get(type).add(emitter);

        emitter.onCompletion(() -> removeEmitter(type, emitter));
        emitter.onTimeout(() -> removeEmitter(type, emitter));
        emitter.onError(throwable -> removeEmitter(type, emitter));

        long currentValue = fetchMetricValue(type);
        Object payload = buildPayload(type, currentValue);
        sendDataEvent(emitter, type, "init", currentValue, payload);

        log.debug("Subscribed to {} metrics stream (lastEventId={})", type, lastEventId);
        return emitter;
    }

    private long fetchMetricValue(MetricType type) {
        LocalDateTime startOfDay = LocalDate.now(MonitoringUtils.KST).atStartOfDay();
        LocalDateTime now = LocalDateTime.now();
        return switch (type) {
            case ACCESS_USERS -> userAggregateHourlyRepository.sumAccessUserCountBetween(startOfDay,
                now);
            case UPLOAD_DOCUMENTS -> documentAggregateHourlyRepository.sumUploadCountBetween(
                startOfDay, now);
            case ERRORS ->
                errorAggregateHourlyRepository.sumTotalErrorCountBetween(startOfDay, now);
        };
    }

    private void sendDataEvent(MetricType type, String eventName, long value) {
        Set<SseEmitter> subscribers = emitters.get(type);
        if (subscribers == null || subscribers.isEmpty()) {
            return;
        }
        Object payload = buildPayload(type, value);
        for (SseEmitter emitter : subscribers) {
            sendDataEvent(emitter, type, eventName, value, payload);
        }
    }

    private Object buildPayload(MetricType type, long value) {
        return switch (type) {
            case ACCESS_USERS -> buildAccessUserEvent(value);
            case UPLOAD_DOCUMENTS -> buildUploadDocumentEvent(value);
            case ERRORS -> buildErrorEvent(value);
        };
    }

    private void sendDataEvent(SseEmitter emitter, MetricType type, String eventName, long value,
        Object payload) {
        try {
            emitter.send(SseEmitter.event()
                .id(Long.toString(value))
                .name(eventName)
                .data(payload));
        } catch (Exception e) {
            log.debug("SSE send failed for {}: {}", type, e.getMessage());
            removeEmitter(type, emitter);
            emitter.completeWithError(e);
        }
    }

    private AccessUserEvent buildAccessUserEvent(long todayTotal) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfDay = now.toLocalDate().atStartOfDay();
        LocalDateTime startOfYesterday = startOfDay.minusDays(1);

        long yesterdayTotal = userAggregateHourlyRepository
            .sumAccessUserCountBetween(startOfYesterday, startOfDay);
        long totalAccessUsers = userAggregateHourlyRepository.sumAccessUserCount();

        double deltaPct = yesterdayTotal != 0
            ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Double.POSITIVE_INFINITY;

        TrendDirection direction = TrendDirection.of(deltaPct);
        return AccessUserEvent.of(todayTotal, totalAccessUsers, deltaPct, direction);
    }

    private UploadDocumentEvent buildUploadDocumentEvent(long todayTotal) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfDay = now.toLocalDate().atStartOfDay();
        LocalDateTime startOfYesterday = startOfDay.minusDays(1);

        long yesterdayTotal = documentAggregateHourlyRepository
            .sumUploadCountBetween(startOfYesterday, startOfDay);
        long totalUploadedDocs = documentAggregateHourlyRepository.sumUploadCount();

        double deltaPct = yesterdayTotal != 0
            ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Double.POSITIVE_INFINITY;

        TrendDirection direction = TrendDirection.of(deltaPct);
        return UploadDocumentEvent.of(todayTotal, totalUploadedDocs, deltaPct, direction);
    }

    private ErrorEvent buildErrorEvent(long todayTotal) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfDay = now.toLocalDate().atStartOfDay();
        LocalDateTime startOfYesterday = startOfDay.minusDays(1);

        long yesterdayTotal = errorAggregateHourlyRepository
            .sumTotalErrorCountBetween(startOfYesterday, startOfDay);
        long totalError = errorAggregateHourlyRepository.sumTotalErrorCount();

        double deltaPct = yesterdayTotal != 0
            ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Double.POSITIVE_INFINITY;

        TrendDirection direction = TrendDirection.of(deltaPct);
        return ErrorEvent.of(todayTotal, totalError, deltaPct, direction);
    }

    private void removeEmitter(MetricType type, SseEmitter emitter) {
        Set<SseEmitter> subscribers = emitters.get(type);
        if (subscribers != null) {
            subscribers.remove(emitter);
        }
    }

    private void broadcastUpdate(MetricType type, long value) {
        sendDataEvent(type, "update", value);
    }

    private LocalDateTime currentHour() {
        return LocalDateTime.now().truncatedTo(ChronoUnit.HOURS);
    }

    private int toInt(long value) {
        if (value > Integer.MAX_VALUE) {
            return Integer.MAX_VALUE;
        }
        if (value < Integer.MIN_VALUE) {
            return Integer.MIN_VALUE;
        }
        return (int) value;
    }

    private enum MetricType {
        ACCESS_USERS,
        UPLOAD_DOCUMENTS,
        ERRORS
    }
}

