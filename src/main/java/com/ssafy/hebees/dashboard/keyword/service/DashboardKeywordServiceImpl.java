package com.ssafy.hebees.dashboard.keyword.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.agentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.agentPrompt.repository.AgentPromptRepository;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.service.LlmChatGateway;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordListRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordRegisterRequest;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse.TrendKeyword;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordRegisterResponse;
import com.ssafy.hebees.dashboard.keyword.entity.KeywordAggregateDaily;
import com.ssafy.hebees.dashboard.keyword.repository.KeywordAggregateDailyRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import jakarta.annotation.PostConstruct;
import java.time.LocalDate;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class DashboardKeywordServiceImpl implements DashboardKeywordService {
    private static final String PROMPT_NAME = "KeywordExtraction";
    private static final String PROMPT_FALLBACK = "You are a Korean keyword extractor. Read the user's sentence and return only the core keywords as a JSON array with 1 to 7 string items. Example: [\"keyword1\", \"keyword2\"]. Do not include any explanations, numbering, or additional text.";

    private final KeywordAggregateDailyRepository keywordAggregateDailyRepository;
    private final LlmChatGateway llmChatGateway;
    private final AgentPromptRepository agentPromptRepository;
    private final ObjectMapper objectMapper;
    private final StrategyRepository strategyRepository;

    private AgentPrompt agentPrompt;

    @PostConstruct
    private void init() {
        agentPrompt = agentPromptRepository.findByNameIgnoreCase(PROMPT_NAME)
            .orElseGet(() -> {
                AgentPrompt created = AgentPrompt.builder()
                    .name(PROMPT_NAME)
                    .content(PROMPT_FALLBACK)
                    .llm(strategyRepository.findByNameAndCodeStartingWith("GPT-4o", "GEN").orElseThrow(()->{
                        log.error("LLM GPT-4o strategy not found");
                        return new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
                    }))
                    .build();
                return agentPromptRepository.save(Objects.requireNonNull(created));
            });
    }


    @Override
    @Transactional(readOnly = true)
    public TrendKeywordListResponse getKeywords(TrendKeywordListRequest request) {
        LocalDate end = LocalDate.now();
        LocalDate start = end.minusDays(request.scale() - 1);

        List<TrendKeyword> topKeywords = keywordAggregateDailyRepository
            .sumTopKeywords(start, end, request.topK());

        if (topKeywords.isEmpty()) {
            return new TrendKeywordListResponse(new Timeframe(start, end), List.of());
        }

        long min = topKeywords.stream().map(TrendKeyword::count).min(Long::compareTo).orElse(0L);
        long max = topKeywords.stream().map(TrendKeyword::count).max(Long::compareTo).orElse(0L);
        long diff = Math.max(1, max - min);

        List<TrendKeyword> normalized = topKeywords.stream()
            .map(keyword -> new TrendKeyword(
                keyword.text(),
                keyword.count(),
                (float) (keyword.count() - min) / diff
            ))
            .toList();

        return new TrendKeywordListResponse(new Timeframe(start, end), normalized);
    }

    @Override
    public TrendKeywordRegisterResponse registerKeywords(TrendKeywordRegisterRequest request) {
        String query = request.query();
        if (!StringUtils.hasText(query)) {
            return toResponse(List.of());
        }

        LocalDate today = LocalDate.now();
        Set<String> extracted = extractKeywords(query);
        Set<String> normalizedKeywords = new LinkedHashSet<>();

        // 키워드 추출에 성공하면 키워드를 그렇지 않다면 쿼리를 등록
        if (extracted.isEmpty()) {
            extracted.add(query);
        }

        for (String raw : extracted) {
            String keyword = normalizeKeyword(raw);
            if (StringUtils.hasText(keyword)) {
                normalizedKeywords.add(keyword);
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

        return toResponse(List.copyOf(normalizedKeywords));
    }

    private Set<String> extractKeywords(String query) {
        UUID llmNo = agentPrompt.getLlm().getStrategyNo();
        String prompt = agentPrompt.getContent();

        try {
            LlmChatResult result = llmChatGateway
                .chatWithSystem(llmNo,
                    List.of(
                        new LlmChatMessage("system", prompt),
                        new LlmChatMessage("user", query)
                    )
                );
            String content = result != null ? result.content() : null;
            log.info("키워드 추출 에이전트 답변: content={}", content);
            return parseKeywordContent(content);
        } catch (Exception e) {
            log.warn("LLM 키워드 추출 실패: {}", e.getMessage());
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
        } catch (Exception e) {
            log.warn("키워드 JSON 파싱 실패: {}", e.getMessage());
        }

        return Set.of();
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

    private static TrendKeywordRegisterResponse toResponse(List<String> keywords) {
        return new TrendKeywordRegisterResponse(keywords);
    }
}
