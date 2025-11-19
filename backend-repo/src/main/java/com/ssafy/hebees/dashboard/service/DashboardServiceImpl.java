package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalUsersResponse;
import com.ssafy.hebees.dashboard.dto.response.TrendDirection;
import com.ssafy.hebees.dashboard.repository.DocumentAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.ErrorAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UserAggregateHourlyRepository;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DashboardServiceImpl implements DashboardService {

    private static final long HOURS_24 = 24L;

    private final UserAggregateHourlyRepository userAggregateHourlyRepository;
    private final DocumentAggregateHourlyRepository documentAggregateHourlyRepository;
    private final ErrorAggregateHourlyRepository errorAggregateHourlyRepository;

    @Override
    public Change24hResponse getAccessUsersChange24h() {
        Window window = Window.current();

        Long current = userAggregateHourlyRepository.sumAccessUserCountBetween(
            window.currentStart(), window.currentEnd());
        Long previous = userAggregateHourlyRepository.sumAccessUserCountBetween(
            window.previousStart(), window.currentStart());

        return toChange24hResponse(
            current != null ? current : 0L,
            previous != null ? previous : 0L,
            window.now());
    }

    @Override
    public Change24hResponse getUploadDocumentsChange24h() {
        Window window = Window.current();

        Long current = documentAggregateHourlyRepository.sumUploadCountBetween(
            window.currentStart(), window.currentEnd());
        Long previous = documentAggregateHourlyRepository.sumUploadCountBetween(
            window.previousStart(), window.currentStart());

        return toChange24hResponse(
            current != null ? current : 0L,
            previous != null ? previous : 0L,
            window.now());
    }

    @Override
    public Change24hResponse getErrorsChange24h() {
        Window window = Window.current();

        Long current = errorAggregateHourlyRepository.sumTotalErrorCountBetween(
            window.currentStart(), window.currentEnd());
        Long previous = errorAggregateHourlyRepository.sumTotalErrorCountBetween(
            window.previousStart(), window.currentStart());

        return toChange24hResponse(
            current != null ? current : 0L,
            previous != null ? previous : 0L,
            window.now());
    }

    @Override
    public TotalUsersResponse getTotalUsers() {
        LocalDateTime asOf = LocalDateTime.now();
        long total = userAggregateHourlyRepository.sumAccessUserCount();
        return TotalUsersResponse.of(total, asOf);
    }

    @Override
    public TotalDocumentsResponse getTotalUploadDocuments() {
        LocalDateTime asOf = LocalDateTime.now();
        long total = documentAggregateHourlyRepository.sumUploadCount();
        return TotalDocumentsResponse.of(total, asOf);
    }

    @Override
    public TotalErrorsResponse getTotalErrors() {
        LocalDateTime asOf = LocalDateTime.now();
        long total = errorAggregateHourlyRepository.sumTotalErrorCount();
        return TotalErrorsResponse.of(total, asOf);
    }

    private static Change24hResponse toChange24hResponse(Long todayTotal, Long yesterdayTotal,
        LocalDateTime asOf) {
        double delta = yesterdayTotal != 0 ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Float.POSITIVE_INFINITY;

        return new Change24hResponse(
            todayTotal,
            yesterdayTotal,
            (float) delta,
            TrendDirection.of(delta),
            asOf
        );
    }

    private record Window(LocalDateTime now, LocalDateTime currentStart, LocalDateTime currentEnd) {

        private static Window current() {
            LocalDateTime now = LocalDateTime.now();
            LocalDateTime currentStart = now.toLocalDate().atStartOfDay();
            LocalDateTime currentEnd = currentStart.plusDays(1);
            return new Window(now, currentStart, currentEnd);
        }

        private LocalDateTime previousStart() {
            return currentStart.minusDays(1);
        }
    }

}

