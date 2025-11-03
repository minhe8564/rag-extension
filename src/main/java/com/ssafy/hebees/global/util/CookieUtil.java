package com.ssafy.hebees.global.util;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.Base64;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;
import org.springframework.util.SerializationUtils;

@Component
public class CookieUtil {

    @Value("${spring.profiles.active}")
    private String activeProfile;

    // HttpOnly + Secure 쿠키 추가
    public void addHttpOnlyCookie(HttpServletResponse response, String name, String value,
        int maxAge) {
        boolean isProd = activeProfile.equalsIgnoreCase("prod");

        ResponseCookie cookie = ResponseCookie.from(name, value)
            .path("/")
            .maxAge(maxAge / 1000) // maxAge는 초 단위
            .httpOnly(true)
            .secure(isProd)
            .sameSite(isProd ? "None" : "Lax")
            .build();

        response.addHeader("Set-Cookie", cookie.toString());
    }

    public void deleteCookie(HttpServletResponse response, String name) {
        boolean isProd = activeProfile.equalsIgnoreCase("prod");

        ResponseCookie cookie = ResponseCookie.from(name, "")
            .path("/")
            .maxAge(0)
            .httpOnly(true)
            .secure(isProd)
            .sameSite(isProd ? "None" : "Lax")
            .build();

        response.addHeader("Set-Cookie", cookie.toString());
    }

    public String getCookieValue(HttpServletRequest request, String name) {
        Cookie[] cookies = request.getCookies();

        if (cookies == null) {
            return null;
        }

        for (Cookie cookie : cookies) {
            if (name.equals(cookie.getName())) {
                return cookie.getValue();
            }
        }
        return null;
    }

    // 객체를 직렬화해 쿠키의 값으로 반환
    public String serialize(Object obj) {
        return Base64.getUrlEncoder()
            .encodeToString(SerializationUtils.serialize(obj));
    }

    // 쿠키를 역직렬화해 객체로 변환
    public <T> T deserialize(Cookie cookie, Class<T> cls) {
        return cls.cast(
            SerializationUtils.deserialize(
                Base64.getUrlDecoder().decode(cookie.getValue())
            )
        );
    }
}
