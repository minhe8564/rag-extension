package com.ssafy.hebees.dashboard.keyword.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.chat.client.RunpodClient;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordCreateRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordListRequest;
import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse.TrendKeyword;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordCreateResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse;
import com.ssafy.hebees.dashboard.entity.KeywordAggregateDaily;
import com.ssafy.hebees.dashboard.keyword.repository.KeywordAggregateDailyRepository;
import com.ssafy.hebees.AgentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.AgentPrompt.repository.AgentPromptRepository;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DashboardKeywordServiceImpl implements DashboardKeywordService {

    private final KeywordAggregateDailyRepository keywordAggregateDailyRepository;
    private final RunpodClient runpodClient;
    private final ObjectMapper objectMapper;
    private final AgentPromptRepository agentPromptRepository;

    @Override
    public TrendKeywordListResponse getTrendKeywords(TrendKeywordListRequest request) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(request.scale() - 1);

        List<TrendKeyword> topKeywords = keywordAggregateDailyRepository.sumTopKeywords(start, end,
            request.topK());

        if (topKeywords.isEmpty()) {
            return new TrendKeywordListResponse(new Timeframe(start, end), List.of());
        }

        long min = topKeywords.stream().map(TrendKeyword::count).min(Long::compareTo).orElse(0L);
        long max = topKeywords.stream().map(TrendKeyword::count).max(Long::compareTo).orElse(0L);
        long diff = Math.max(1, max - min);

        List<TrendKeyword> normalized = topKeywords.stream()
            .map(keyword -> new TrendKeyword(keyword.text(), keyword.count(),
                (float) (keyword.count() - min) / diff))
            .toList();

        return new TrendKeywordListResponse(new Timeframe(start, end), normalized);
    }

    @Override
    @Transactional
    public TrendKeywordCreateResponse recordTrendKeywords(TrendKeywordCreateRequest request) {
        String query = request.query();
        if (!StringUtils.hasText(query)) {
            return TrendKeywordCreateResponse.of(List.of());
        }

        LocalDate today = LocalDate.now();
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
                        keywordAggregateDailyRepository.save(Objects.requireNonNull(created));
                    }
                );
        }

        return TrendKeywordCreateResponse.of(List.copyOf(normalizedKeywords));
    }

    private Set<String> extractKeywords(String query) {
        String prompt = "You are a Korean keyword extractor. Read the user's sentence and return only the core keywords in a JSON array with 1 to 7 items. Example: [\"keyword1\", \"keyword2\"]. Do not include any unnecessary explanations.";

        AgentPrompt agentPrompt = agentPromptRepository.findByName("KeywordExtraction")
            .orElse(null);
        if (agentPrompt != null && StringUtils.hasText(agentPrompt.getContent())) {
            prompt = agentPrompt.getContent();
        }

        try {
            RunpodChatResult result = runpodClient.chat(List.of(
                RunpodChatMessage.of("system", prompt),
                RunpodChatMessage.of("user", query)
            ));

            String content = result != null ? result.content() : null;
            log.info("키워드 추출 에이전트 답변: content={}", content);
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

}


