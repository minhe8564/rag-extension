package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.QueryGroup;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface QueryGroupRepository extends JpaRepository<QueryGroup, UUID> {

    List<QueryGroup> findByIsDefault(boolean aDefault);
}

