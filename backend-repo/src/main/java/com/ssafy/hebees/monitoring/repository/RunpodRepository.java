package com.ssafy.hebees.monitoring.repository;

import com.ssafy.hebees.chat.entity.MessageError;
import com.ssafy.hebees.monitoring.entity.Runpod;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RunpodRepository extends JpaRepository<Runpod, UUID>, RunpodRepositoryCustom {

}
