package com.ssafy.hebees.common.util;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.util.UUID;

public final class UserValidationUtil {

    private UserValidationUtil() {
    }

    public static UUID requireUser(UUID userNo) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.INPUT_NULL);
        }
        return userNo;
    }
}


