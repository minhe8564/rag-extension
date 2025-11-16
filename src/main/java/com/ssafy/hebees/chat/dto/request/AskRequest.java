package com.ssafy.hebees.chat.dto.request;

import com.mongodb.lang.Nullable;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import java.util.UUID;
import org.springframework.util.StringUtils;

@Schema(description = "질문 요청 DTO")
public record AskRequest(
    @Nullable
    @Schema(description = "질문할 세션 ID")
    UUID sessionNo,

    @Nullable
    @Schema(description = "사용할 LLM ID")
    UUID llmNo,

    @Nullable
    @Schema(description = "사용할 LLM 이름")
    String model,

    @Nullable
    @Schema(description = "질문 내용 (삭제 예정)")
    String content,

    @Nullable
    @Schema(description = "질문 내용")
    String query
) {

    public AskRequest {
        if (!StringUtils.hasText(query) && !StringUtils.hasText(content)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }
        if (!StringUtils.hasText(model) && llmNo == null) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }
    }

    public String getQuery() {
        return StringUtils.hasText(query) ? query : content;
    }
}
