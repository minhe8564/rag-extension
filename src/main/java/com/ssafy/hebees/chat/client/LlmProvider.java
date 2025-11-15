package com.ssafy.hebees.chat.client;

import java.util.Arrays;
import java.util.Locale;
import java.util.Optional;
import java.util.Set;

public enum LlmProvider {

    CHATGPT(Set.of("openai", "chatgpt", "gpt")),
    GEMINI(Set.of("gemini", "google")),
    CLAUDE(Set.of("claude", "anthropic")),
    RUNPOD(Set.of("runpod", "ollama"));

    private final Set<String> keywords;

    LlmProvider(Set<String> keywords) {
        this.keywords = keywords;
    }

    public static Optional<LlmProvider> fromIdentifier(String identifier) {
        if (identifier == null || identifier.isBlank()) {
            return Optional.empty();
        }

        String normalized = identifier.toLowerCase(Locale.ROOT);
        return Arrays.stream(values())
            .filter(provider -> provider.matches(normalized))
            .findFirst();
    }

    private boolean matches(String identifier) {
        return keywords.stream().anyMatch(identifier::contains);
    }
}

