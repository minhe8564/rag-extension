package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;

@Schema(description = "모델별 비용 산정 응답 DTO")
public record ModelPriceResponse(
    @Schema(description = "응답 생성 시각 (KST)", example = "2025-01-01T09:00:00")
    LocalDateTime timestamp,
    @Schema(description = "모든 모델의 총 비용 (USD)", example = "12.345678")
    BigDecimal grandPriceUsd,
    @Schema(description = "모델별 비용 (입력 토큰 사용량 x 입력 토큰 비용 + 출력 토큰 사용량 x 출력 토큰 비용)")
    List<Item> models
) {

    private static final int DEFAULT_SCALE = 6;

    public ModelPriceResponse {
        grandPriceUsd = normalize(grandPriceUsd);
        models = models == null ? List.of() : List.copyOf(models);
    }

    public static ModelPriceResponse of(LocalDateTime timestamp, List<Item> models) {
        List<Item> safeModels = models == null ? List.of() : List.copyOf(models);
        BigDecimal grand = safeModels.stream()
            .map(Item::totalPriceUsd)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
        return new ModelPriceResponse(timestamp, normalize(grand), safeModels);
    }

    private static BigDecimal normalize(BigDecimal value) {
        if (value == null) {
            return BigDecimal.ZERO.setScale(DEFAULT_SCALE);
        }
        return value.setScale(DEFAULT_SCALE, RoundingMode.HALF_UP);
    }

    @Schema(description = "모델별 비용 정보")
    public record Item(
        @Schema(description = "모델 식별자 또는 이름", example = "gpt-4o")
        String model,
        @Schema(description = "입력 토큰 비용 누적액 (USD)", example = "3.210000")
        BigDecimal inputPriceUsd,
        @Schema(description = "출력 토큰 비용 누적액 (USD)", example = "2.890000")
        BigDecimal outputPriceUsd,
        @Schema(description = "총 토큰 비용 누적액 (USD)", example = "6.100000")
        BigDecimal totalPriceUsd
    ) {

        public Item {
            inputPriceUsd = normalize(inputPriceUsd);
            outputPriceUsd = normalize(outputPriceUsd);
            totalPriceUsd = normalize(totalPriceUsd != null
                ? totalPriceUsd
                : inputPriceUsd.add(outputPriceUsd));
        }

        public static Item of(String model, BigDecimal inputPriceUsd, BigDecimal outputPriceUsd) {
            BigDecimal normalizedInput = normalize(inputPriceUsd);
            BigDecimal normalizedOutput = normalize(outputPriceUsd);
            BigDecimal total = normalizedInput.add(normalizedOutput);
            return new Item(model, normalizedInput, normalizedOutput, total);
        }
    }
}