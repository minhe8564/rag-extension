package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.dashboard.dto.response.ModelPriceResponse;
import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import com.ssafy.hebees.dashboard.repository.ModelAggregateHourlyRepository;
import com.ssafy.hebees.ragsetting.entity.ModelPrice;
import com.ssafy.hebees.ragsetting.repository.ModelPriceRepository;
import jakarta.annotation.Nullable;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArraySet;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AnalyticsExpenseStreamServiceImpl implements AnalyticsExpenseStreamService {

    private static final int PRICE_SCALE = 6;
    private static final BigDecimal TOKENS_PER_THOUSAND = BigDecimal.valueOf(1_000L);

    private final ModelAggregateHourlyRepository modelAggregateHourlyRepository;
    private final ModelPriceRepository modelPriceRepository;

    private final Set<SseEmitter> emitters = new CopyOnWriteArraySet<>();
    private volatile ModelPriceResponse lastBroadcast;

    @Override
    public SseEmitter subscribeExpenseStream(String lastEventId) {
        SseEmitter emitter = new SseEmitter(0L);
        emitters.add(emitter);

        emitter.onCompletion(() -> removeEmitter(emitter));
        emitter.onTimeout(() -> removeEmitter(emitter));
        emitter.onError(throwable -> removeEmitter(emitter));

        ModelPriceResponse snapshot = loadCurrentExpenseSnapshot();
        if (lastBroadcast == null) {
            lastBroadcast = snapshot;
        }
        sendDataEvent(emitter, "init", snapshot);

        log.debug("Subscribed to analytics expense stream (lastEventId={})", lastEventId);
        return emitter;
    }

    @Override
    public void notifyExpenseChanged() {
        if (emitters.isEmpty()) {
            return;
        }

        try {
            ModelPriceResponse snapshot = loadCurrentExpenseSnapshot();
            if (!snapshot.equals(lastBroadcast)) {
                lastBroadcast = snapshot;
                broadcastUpdate(snapshot);
            }
        } catch (Exception e) {
            log.warn("Failed to broadcast analytics expense snapshot: {}", e.getMessage(), e);
        }
    }

    private void broadcastUpdate(ModelPriceResponse snapshot) {
        for (SseEmitter emitter : emitters) {
            sendDataEvent(emitter, "update", snapshot);
        }
    }

    private String resolveEventId(ModelPriceResponse payload) {
        LocalDateTime timestamp = payload.timestamp();
        if (timestamp != null) {
            return timestamp.toString();
        }
        return Long.toString(System.currentTimeMillis());
    }

    private void sendDataEvent(SseEmitter emitter, String eventName, ModelPriceResponse payload) {
        try {
            Objects.requireNonNull(emitter, "emitter must not be null");
            String safeEventName = eventName != null ? eventName : "update";
            ModelPriceResponse safePayload = Objects.requireNonNull(payload,
                "payload must not be null");

            ModelPriceResponse response = safePayload;
            String eventId = Objects.requireNonNull(resolveEventId(safePayload));

            emitter.send(SseEmitter.event()
                .id(eventId)
                .name(safeEventName)
                .data((Object) Objects.requireNonNull(response)));
        } catch (Exception e) {
            log.debug("SSE send failed for analytics expense stream: {}", e.getMessage());
            removeEmitter(emitter);
            emitter.completeWithError(e);
        }
    }

    private void removeEmitter(SseEmitter emitter) {
        emitters.remove(emitter);
        log.debug("Removed analytics expense stream emitter. Remaining={}", emitters.size());
    }

    private ModelPriceResponse loadCurrentExpenseSnapshot() {
        LocalDateTime now = LocalDateTime.now(MonitoringUtils.KST);
        LocalDate today = now.toLocalDate();
        LocalDateTime startOfDay = today.atStartOfDay();

        List<ModelAggregateHourly> aggregates = modelAggregateHourlyRepository.findBetween(
            startOfDay, now);

        if (aggregates.isEmpty()) {
            return ModelPriceResponse.of(now, List.of());
        }

        Map<UUID, ModelAccumulator> accumulators = new HashMap<>();
        for (ModelAggregateHourly aggregate : aggregates) {
            UUID llmNo = aggregate.getLlmNo();
            if (llmNo == null) {
                continue;
            }

            ModelAccumulator accumulator = accumulators.computeIfAbsent(llmNo,
                id -> new ModelAccumulator(resolveModelName(aggregate)));

            accumulator.addInputTokens(aggregate.getInputTokens());
            accumulator.addOutputTokens(aggregate.getOutputTokens());
            accumulator.updateModelName(aggregate.getLlmName());
        }

        if (accumulators.isEmpty()) {
            return ModelPriceResponse.of(now, List.of());
        }

        Iterable<UUID> modelIds = Objects.requireNonNull(List.copyOf(accumulators.keySet()));
        Map<UUID, ModelPrice> pricesByModel = modelPriceRepository.findAllById(modelIds).stream()
            .collect(Collectors.toMap(ModelPrice::getLlmNo, Function.identity()));

        List<ModelPriceResponse.Item> items = accumulators.entrySet().stream()
            .map(entry -> toResponseItem(entry.getKey(), entry.getValue(),
                pricesByModel.get(entry.getKey())))
            .sorted(Comparator.comparing(ModelPriceResponse.Item::totalPriceUsd).reversed())
            .toList();

        return ModelPriceResponse.of(now, items);
    }

    private ModelPriceResponse.Item toResponseItem(UUID llmNo, ModelAccumulator accumulator,
        @Nullable ModelPrice price) {
        BigDecimal inputUnitPrice = price != null ? price.getInputTokenPricePer1kUsd() : null;
        BigDecimal outputUnitPrice = price != null ? price.getOutputTokenPricePer1kUsd() : null;

        BigDecimal inputCost = computeCost(accumulator.inputTokens(), inputUnitPrice);
        BigDecimal outputCost = computeCost(accumulator.outputTokens(), outputUnitPrice);

        String modelLabel = accumulator.modelName();
        if (modelLabel == null || modelLabel.isBlank()) {
            modelLabel = llmNo != null ? llmNo.toString() : "UNKNOWN";
        }

        return ModelPriceResponse.Item.of(modelLabel, inputCost, outputCost);
    }

    private BigDecimal computeCost(long tokens, @Nullable BigDecimal unitPrice) {
        if (unitPrice == null || unitPrice.signum() == 0 || tokens <= 0) {
            return BigDecimal.ZERO.setScale(PRICE_SCALE);
        }

        BigDecimal normalizedPrice = unitPrice.setScale(PRICE_SCALE, RoundingMode.HALF_UP);
        BigDecimal tokenAmount = BigDecimal.valueOf(Math.max(tokens, 0L));

        return normalizedPrice.multiply(tokenAmount)
            .divide(TOKENS_PER_THOUSAND, PRICE_SCALE, RoundingMode.HALF_UP);
    }

    private String resolveModelName(ModelAggregateHourly aggregate) {
        String name = aggregate.getLlmName();
        if (name != null && !name.isBlank()) {
            return name;
        }
        UUID llmNo = aggregate.getLlmNo();
        return llmNo != null ? llmNo.toString() : "UNKNOWN";
    }

    private static class ModelAccumulator {

        private String modelName;
        private long inputTokens;
        private long outputTokens;

        private ModelAccumulator(String modelName) {
            this.modelName = modelName;
        }

        void addInputTokens(Long tokens) {
            if (tokens != null) {
                inputTokens += Math.max(tokens, 0L);
            }
        }

        void addOutputTokens(Long tokens) {
            if (tokens != null) {
                outputTokens += Math.max(tokens, 0L);
            }
        }

        void updateModelName(String candidate) {
            if (candidate != null && !candidate.isBlank()) {
                modelName = candidate;
            }
        }

        String modelName() {
            return modelName;
        }

        long inputTokens() {
            return inputTokens;
        }

        long outputTokens() {
            return outputTokens;
        }
    }
}

