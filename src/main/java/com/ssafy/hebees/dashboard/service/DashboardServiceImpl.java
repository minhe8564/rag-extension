package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.repository.DocumentAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.ErrorAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.repository.UserAggregateHourlyRepository;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.function.BiFunction;
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
        return buildChange24hResponse(userAggregateHourlyRepository::sumAccessUserCountBetween);
    }

    @Override
    public Change24hResponse getUploadDocumentsChange24h() {
        return buildChange24hResponse(documentAggregateHourlyRepository::sumUploadCountBetween);
    }

    @Override
    public TotalDocumentsResponse getTotalUploadDocuments() {
        LocalDateTime asOf = LocalDateTime.now();
        int total = toInt(documentAggregateHourlyRepository.sumUploadCount());
        return TotalDocumentsResponse.of(total, asOf);
    }

    @Override
    public Change24hResponse getErrorsChange24h() {
        return buildChange24hResponse(errorAggregateHourlyRepository::sumTotalErrorCountBetween);
    }

    @Override
    public TotalErrorsResponse getTotalErrors() {
        LocalDateTime asOf = LocalDateTime.now();
        int total = toInt(errorAggregateHourlyRepository.sumTotalErrorCount());
        return TotalErrorsResponse.of(total, asOf);
    }

    private Change24hResponse buildChange24hResponse(
        BiFunction<LocalDateTime, LocalDateTime, Long> sumBetween) {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime referenceHour = now.truncatedTo(ChronoUnit.HOURS);

        LocalDateTime currentWindowStart = referenceHour.minusHours(HOURS_24);
        LocalDateTime previousWindowStart = currentWindowStart.minusHours(HOURS_24);

        int current = toInt(sumBetween.apply(currentWindowStart, referenceHour));
        int previous = toInt(sumBetween.apply(previousWindowStart, currentWindowStart));

        return toChange24hResponse(current, previous, now);
    }

    private int toInt(Long value) {
        if (value == null) {
            return 0;
        }
        return Math.toIntExact(value);
    }

    private static Change24hResponse toChange24hResponse(Integer todayTotal, Integer yesterdayTotal,
        LocalDateTime asOf) {
        double delta = yesterdayTotal != 0 ? (double) (todayTotal - yesterdayTotal) / yesterdayTotal
            : Float.POSITIVE_INFINITY;

        return new Change24hResponse(
            todayTotal,
            yesterdayTotal,
            (float) delta,
            delta >= 0 ? "up" : "down",
            asOf
        );
    }
}

