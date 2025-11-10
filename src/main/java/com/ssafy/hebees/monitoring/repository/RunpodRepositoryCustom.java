package com.ssafy.hebees.monitoring.repository;

import com.ssafy.hebees.monitoring.entity.Runpod;
import java.util.Optional;

/**
 * QueryDSL을 사용한 Runpod 커스텀 Repository 인터페이스
 */
public interface RunpodRepositoryCustom {

    /**
     * 이름으로 Runpod 조회 (QueryDSL)
     *
     * @param name Runpod 이름
     * @return Runpod 정보 (Optional)
     */
    Optional<Runpod> findByName(String name);
}
