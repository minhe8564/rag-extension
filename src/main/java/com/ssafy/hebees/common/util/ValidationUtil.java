package com.ssafy.hebees.common.util;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;

public final class ValidationUtil {

    private ValidationUtil() {
    }

    public static <T> T require(T value) {
        if (value == null) {
            throw new BusinessException(ErrorCode.INPUT_NULL);
        }
        return value;
    }
}

