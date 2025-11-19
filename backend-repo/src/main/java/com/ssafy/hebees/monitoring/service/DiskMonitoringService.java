package com.ssafy.hebees.monitoring.service;

import com.ssafy.hebees.monitoring.dto.response.StorageInfoResponse;
import com.ssafy.hebees.monitoring.dto.response.StorageListResponse;
import com.ssafy.hebees.common.util.MonitoringUtils;
import lombok.extern.slf4j.Slf4j;
import oshi.SystemInfo;
import oshi.software.os.FileSystem;
import oshi.software.os.OSFileStore;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
public class DiskMonitoringService {

    private final SystemInfo systemInfo = new SystemInfo();

    private StorageInfoResponse convertToStorageInfo(OSFileStore fileStore) {
        try {
            String path = fileStore.getMount();
            long totalBytes = fileStore.getTotalSpace();
            long usableBytes = fileStore.getUsableSpace();
            long usedBytes = totalBytes - usableBytes;

            double totalGB = MonitoringUtils.bytesToGb(totalBytes);
            double usedGB = MonitoringUtils.bytesToGb(usedBytes);
            double usagePercent = totalGB > 0
                ? MonitoringUtils.round((usedGB / totalGB) * 100.0, 2)
                : 0.0;

            return new StorageInfoResponse(path, totalGB, usedGB, usagePercent);
        } catch (Exception e) {
            log.warn("파일시스템 정보를 가져오는 중 오류 발생: {}", fileStore.getMount(), e);
            return null;
        }
    }

    public StorageListResponse getStorageInfo() {
        String timestamp = MonitoringUtils.getKstTimestamp();
        FileSystem fileSystem = systemInfo.getOperatingSystem().getFileSystem();
        List<OSFileStore> fileStores = fileSystem.getFileStores();

        List<StorageInfoResponse> fileSystems = fileStores.stream()
            .map(this::convertToStorageInfo)
            .filter(info -> info != null)
            .sorted((a, b) -> {
                if (a.path().equals("/")) {
                    return -1;
                }
                if (b.path().equals("/")) {
                    return 1;
                }
                return a.path().compareTo(b.path());
            })
            .collect(Collectors.toList());

        return new StorageListResponse(timestamp, fileSystems);
    }
}

