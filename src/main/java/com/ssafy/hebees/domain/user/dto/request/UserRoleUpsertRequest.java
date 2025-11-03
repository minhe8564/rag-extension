package com.ssafy.hebees.domain.user.dto.request;

import com.ssafy.hebees.domain.user.entity.UserRole;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.*;

import java.util.Locale;

@Schema(description = "사용자 역할 생성 DTO")
public record UserRoleUpsertRequest(
    @NotNull(message = "권한 모드는 필수입니다.")
    @PositiveOrZero(message = "권한 모드는 0 이상이어야 합니다.")
    @Schema(description = "권한 모드 (0 이상 정수)", example = "1", minimum = "0", requiredMode = Schema.RequiredMode.REQUIRED)
    Integer mode,

    @NotNull(message = "역할명은 필수입니다.")
    @NotBlank(message = "역할명은 필수입니다.")
    @Size(min = 1, max = 20, message = "역할명은 1자 이상 20자 이하여야 합니다.")
    @Pattern(regexp = "^[A-Z_]+$", message = "역할명은 대문자와 언더스코어(_)만 사용할 수 있습니다.")
    @Schema(description = "역할명", example = "ADMIN", minLength = 1, maxLength = 20, requiredMode = Schema.RequiredMode.REQUIRED)
    String name
) {

    public UserRoleUpsertRequest {
        if (name != null) {
            name = name.trim();
            if (!name.isEmpty()) {
                name = name.toUpperCase(Locale.ROOT);
            }
        }
    }

    public UserRole toEntity() {
        return UserRole.builder()
            .mode(mode)
            .name(name)
            .build();
    }
}
