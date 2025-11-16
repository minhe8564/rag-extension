package com.ssafy.hebees.common.util;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import jakarta.annotation.Nullable;
import org.springframework.util.StringUtils;

public final class ValidationUtil {

    private ValidationUtil() {
    }

    public static <T> T require(@Nullable T value) {
        if (value == null) {
            throw new BusinessException(ErrorCode.INPUT_NULL);
        }
        return value;
    }

    public static String require(@Nullable String value) {
        if (!StringUtils.hasText(value)) {
            throw new BusinessException(ErrorCode.INPUT_BLANK);
        }
        return value.trim();
    }

    public static String orElse(@Nullable String value, String defaultValue) {
        return StringUtils.hasText(value) ? value.trim() : defaultValue;
    }
}

