package com.ssafy.hebees.ragsetting.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "AGENT_PROMPT")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AgentPrompt extends BaseEntity {

    @Id
    @Column(name = "AGENT_PROMPT_NO", columnDefinition = "BINARY(16)", nullable = false, updatable = false)
    private UUID agentPromptNo;

    @Column(name = "NAME", length = 100, nullable = false, unique = true)
    private String name;

    @Column(name = "DESCRIPTION", length = 255)
    private String description;

    @Column(name = "CONTENT", columnDefinition = "TEXT", nullable = false)
    private String content;

    @PrePersist
    private void prePersist() {
        if (agentPromptNo == null) {
            agentPromptNo = UUID.randomUUID();
        }
    }

    public void update(String name, String description, String content) {
        this.name = name;
        this.description = description;
        this.content = content;
    }
}

