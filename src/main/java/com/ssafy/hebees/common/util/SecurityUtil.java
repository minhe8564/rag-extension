package com.ssafy.hebees.common.util;

import com.ssafy.hebees.user.entity.UserRole;
import jakarta.servlet.http.HttpServletRequest;
import java.util.Optional;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component
public class SecurityUtil {

    private static final String JWT_TOKEN_HEADER = "X-JWT-Token";

    private static JwtDecoder jwtDecoder;

    @Autowired
    public void setJwtDecoder(JwtDecoder jwtDecoder) {
        SecurityUtil.jwtDecoder = jwtDecoder;
    }

    /**
     * 현재 사용자의 UUID를 반환합니다. Gateway에서 전달된 JWT 토큰을 디코딩하여 사용자 정보를 추출합니다.
     *
     * @return 사용자 UUID가 있으면 Optional.of(UUID), 없으면 Optional.empty()
     */
    public static Optional<UUID> getCurrentUserUuid() {
        String token = getJwtTokenFromRequest();
        if (token != null && jwtDecoder != null) {
            return jwtDecoder.extractUserUuid(token);
        }
        return Optional.empty();
    }

    /**
     * 현재 사용자의 역할을 반환합니다. Gateway에서 전달된 JWT 토큰을 디코딩하여 사용자 역할을 추출합니다.
     *
     * @return 사용자 역할이 있으면 Optional.of(UserRole), 없으면 Optional.empty()
     */
    public static Optional<UserRole> getCurrentUserRole() {
        String token = getJwtTokenFromRequest();
        if (token != null && jwtDecoder != null) {
            return jwtDecoder.extractUserRole(token);
        }
        return Optional.empty();
    }

    /**
     * 현재 사용자가 ADMIN 역할인지 확인합니다.
     *
     * @return ADMIN이면 true, 아니면 false
     */
    public static boolean isAdmin() {
        return getCurrentUserRole().map(role -> role == UserRole.ADMIN).orElse(false);
    }

    /**
     * 현재 사용자가 안경점 역할인지 확인합니다.
     *
     * @return OPTICAL_SHOP이면 true, 아니면 false
     */
    public static boolean isOpticalShop() {
        return getCurrentUserRole().map(role -> role == UserRole.OPTICAL_SHOP).orElse(false);
    }

    /**
     * 현재 사용자가 협력사 역할인지 확인합니다.
     *
     * @return PARTNER이면 true, 아니면 false
     */
    public static boolean isPartner() {
        return getCurrentUserRole().map(role -> role == UserRole.PARTNER).orElse(false);
    }

    /**
     * 현재 사용자가 제조사 역할인지 확인합니다.
     *
     * @return MANUFACTURER이면 true, 아니면 false
     */
    public static boolean isManufacturer() {
        return getCurrentUserRole().map(role -> role == UserRole.MANUFACTURER).orElse(false);
    }

    /**
     * 현재 HTTP 요청에서 JWT 토큰을 추출합니다.
     *
     * @return JWT 토큰, 없으면 null
     */
    private static String getJwtTokenFromRequest() {
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();
                return request.getHeader(JWT_TOKEN_HEADER);
            }
        } catch (Exception e) {
            // 로그 출력 가능
        }
        return null;
    }
}
