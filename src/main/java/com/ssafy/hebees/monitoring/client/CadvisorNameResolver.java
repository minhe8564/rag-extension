package com.ssafy.hebees.monitoring.client;

import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import lombok.NoArgsConstructor;

/**
 * cAdvisor 컨테이너 이름 해석 및 정규화
 */
@NoArgsConstructor
public class CadvisorNameResolver {

    private static final String[] PREFERRED_LABEL_KEYS = new String[]{
        "io.kubernetes.container.name",
        "io.kubernetes.pod.name",
        "io.kubernetes.deployment.name",
        "io.kubernetes.statefulset.name",
        "io.openshift.serviceName",
        "com.docker.compose.service",
        "io.docker.compose.service",
        "container_label_com_docker_compose_service",
        "container_label_com_docker_swarm_service_name",
        "container_label_io_kubernetes_container_name",
        "container_label_io_kubernetes_pod_name",
        "name"
    };

    /**
     * 별칭 집합 생성 (rawName, aliases, labels에서 변형된 이름들 수집)
     */
    public static Set<String> buildAliasSet(String rawName, java.util.List<String> aliases,
        Map<String, String> labels) {
        LinkedHashSet<String> values = new LinkedHashSet<>();
        addVariants(values, rawName);
        aliases.forEach(alias -> addVariants(values, alias));
        labels.values().forEach(value -> addVariants(values, value));
        values.removeIf(str -> str == null || str.isBlank());
        return values;
    }

    /**
     * 이름의 변형들을 추가 (원본, 숫자 인덱스 제거 버전)
     */
    private static void addVariants(Set<String> values, String raw) {
        String cleaned = sanitize(raw);
        if (cleaned == null || cleaned.isBlank()) {
            return;
        }
        values.add(cleaned);
        String withoutDashIndex = cleaned.replaceAll("[-_][0-9]+$", "");
        if (!withoutDashIndex.isBlank()) {
            values.add(withoutDashIndex);
        }
    }

    /**
     * 표시 이름 결정 (우선순위: labels > aliases > canonical)
     */
    public static String resolveDisplayName(String canonical, Set<String> aliases,
        Map<String, String> labels) {
        for (String key : PREFERRED_LABEL_KEYS) {
            String candidate = labels.get(key);
            candidate = sanitize(candidate);
            if (isUsableDisplayName(candidate)) {
                return candidate;
            }
        }

        for (String alias : aliases) {
            String candidate = sanitize(alias);
            if (isUsableDisplayName(candidate)) {
                return candidate;
            }
        }

        String cleanedCanonical = sanitize(canonical);
        if (isUsableDisplayName(cleanedCanonical)) {
            return cleanedCanonical;
        }
        if (cleanedCanonical != null && !cleanedCanonical.isBlank()) {
            return cleanedCanonical;
        }
        return canonical;
    }

    /**
     * 표시 이름으로 사용 가능한지 확인
     */
    private static boolean isUsableDisplayName(String value) {
        if (value == null || value.isBlank()) {
            return false;
        }
        String lower = value.toLowerCase(Locale.ROOT);
        if (lower.startsWith("system.slice")) {
            return false;
        }
        if (lower.startsWith("kubepods")) {
            return false;
        }
        if (lower.startsWith("docker-")) {
            return false;
        }
        if (lower.startsWith("libpod-")) {
            return false;
        }
        if (lower.matches("[0-9a-f]{12,}")) {
            return false;
        }
        return true;
    }

    /**
     * 컨테이너 이름 정규화 (docker://, containerd:// 등 제거)
     */
    public static String sanitize(String raw) {
        if (raw == null) {
            return null;
        }
        String cleaned = raw.trim();
        while (cleaned.startsWith("/")) {
            cleaned = cleaned.substring(1);
        }
        cleaned = cleaned.replace("docker://", "")
            .replace("containerd://", "");
        if (cleaned.startsWith("docker/")) {
            cleaned = cleaned.substring("docker/".length());
        }
        if (cleaned.startsWith("system.slice/")) {
            cleaned = cleaned.substring("system.slice/".length());
        }
        if (cleaned.endsWith(".scope")) {
            cleaned = cleaned.substring(0, cleaned.length() - ".scope".length());
        }
        if (cleaned.startsWith("docker-") && cleaned.length() > "docker-".length()) {
            String remainder = cleaned.substring("docker-".length());
            if (remainder.matches("[0-9a-f]{8,}")) {
                cleaned = remainder;
            }
        }
        if (cleaned.startsWith("libpod-") && cleaned.length() > "libpod-".length()) {
            String remainder = cleaned.substring("libpod-".length());
            if (remainder.matches("[0-9a-f]{8,}")) {
                cleaned = remainder;
            }
        }
        if (cleaned.startsWith("containerd-") && cleaned.length() > "containerd-".length()) {
            String remainder = cleaned.substring("containerd-".length());
            if (remainder.matches("[0-9a-f]{8,}")) {
                cleaned = remainder;
            }
        }
        return cleaned;
    }
}

