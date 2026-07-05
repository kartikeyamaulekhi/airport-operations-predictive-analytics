package com.kartikeya.airportbackend.seeder;

import com.kartikeya.airportbackend.dto.AirportDTOs.DelayPredictionRequest;
import com.kartikeya.airportbackend.dto.AirportDTOs.DelayPredictionResponse;
import com.kartikeya.airportbackend.repository.PredictionHistoryRepository;
import com.kartikeya.airportbackend.service.AirportService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

/**
 * DataSeeder — runs once on startup and populates the database with
 * realistic historical predictions IF the database is empty.
 *
 * Why this matters: when a recruiter opens your live dashboard for the
 * first time, they see real data immediately — not an empty table.
 * This is standard practice in production demo systems.
 *
 * Implements ApplicationRunner so it runs after the full Spring context
 * is initialized (including JPA and the ML service connection).
 * Idempotent: only seeds if totalPredictions == 0.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class DataSeeder implements ApplicationRunner {

    private final AirportService              airportService;
    private final PredictionHistoryRepository predictionHistoryRepository;

    // Realistic monthly scenarios covering 2 years of operations
    private static final double[][] SEED_DATA = {
        // year,  month, flights, isSummer, isWinter, yearsSince2013, airportAvg, carrierAvg
        {2024,  1,   180,  0, 1, 11, 0.210, 0.195},  // Jan 2024 - winter
        {2024,  2,   165,  0, 0, 11, 0.185, 0.172},  // Feb 2024 - quiet
        {2024,  3,   210,  0, 0, 11, 0.192, 0.180},  // Mar 2024
        {2024,  4,   225,  0, 0, 11, 0.188, 0.175},  // Apr 2024
        {2024,  5,   240,  0, 0, 11, 0.195, 0.182},  // May 2024
        {2024,  6,   310,  1, 0, 11, 0.245, 0.228},  // Jun 2024 - summer peak
        {2024,  7,   340,  1, 0, 11, 0.268, 0.251},  // Jul 2024 - busiest
        {2024,  8,   325,  1, 0, 11, 0.255, 0.239},  // Aug 2024 - summer
        {2024,  9,   285,  0, 0, 11, 0.218, 0.204},  // Sep 2024
        {2024, 10,   270,  0, 0, 11, 0.205, 0.191},  // Oct 2024
        {2024, 11,   295,  0, 0, 11, 0.222, 0.208},  // Nov 2024
        {2024, 12,   350,  0, 1, 11, 0.278, 0.261},  // Dec 2024 - holiday peak
        {2025,  1,   195,  0, 1, 12, 0.215, 0.199},  // Jan 2025
        {2025,  2,   178,  0, 0, 12, 0.188, 0.175},  // Feb 2025
        {2025,  3,   220,  0, 0, 12, 0.196, 0.183},  // Mar 2025
        {2025,  4,   235,  0, 0, 12, 0.191, 0.178},  // Apr 2025
        {2025,  5,   255,  0, 0, 12, 0.198, 0.185},  // May 2025
        {2025,  6,   320,  1, 0, 12, 0.251, 0.235},  // Jun 2025
        {2025,  7,   355,  1, 0, 12, 0.272, 0.255},  // Jul 2025 - peak
        {2025,  8,   338,  1, 0, 12, 0.261, 0.244},  // Aug 2025
        {2025,  9,   292,  0, 0, 12, 0.221, 0.207},  // Sep 2025
        {2025, 10,   278,  0, 0, 12, 0.208, 0.194},  // Oct 2025
        {2025, 11,   305,  0, 0, 12, 0.228, 0.213},  // Nov 2025
        {2025, 12,   362,  0, 1, 12, 0.282, 0.264},  // Dec 2025 - holiday
        {2026,  1,   201,  0, 1, 13, 0.218, 0.202},  // Jan 2026
        {2026,  2,   182,  0, 0, 13, 0.191, 0.178},  // Feb 2026
        {2026,  3,   228,  0, 0, 13, 0.199, 0.186},  // Mar 2026
        {2026,  4,   242,  0, 0, 13, 0.194, 0.181},  // Apr 2026
        {2026,  5,   261,  0, 0, 13, 0.201, 0.188},  // May 2026
        {2026,  6,   328,  1, 0, 13, 0.255, 0.239},  // Jun 2026 - current summer
    };

    @Override
    public void run(ApplicationArguments args) {
        long existingCount = predictionHistoryRepository.count();

        if (existingCount > 0) {
            log.info("[DataSeeder] Database already has {} predictions — skipping seed",
                    existingCount);
            return;
        }

        log.info("[DataSeeder] Empty database detected — seeding {} historical predictions...",
                SEED_DATA.length);

        int seeded = 0;
        int failed = 0;

        for (double[] row : SEED_DATA) {
            try {
                DelayPredictionRequest request = DelayPredictionRequest.builder()
                        .year(row[0])
                        .month(row[1])
                        .arrFlights(row[2])
                        .isSummer(row[3])
                        .isWinterHoliday(row[4])
                        .yearsSince2013(row[5])
                        .airportAvgDelayRate(row[6])
                        .carrierAvgDelayRate(row[7])
                        .build();

                DelayPredictionResponse result = airportService.predictDelay(request);
                seeded++;

                log.debug("[DataSeeder] Seeded {}/{} — {}/{}: status={}, prob={}",
                        seeded, SEED_DATA.length,
                        (int)row[0], (int)row[1],
                        result.getStatus(),
                        result.getHighDelayProbability());

            } catch (Exception e) {
                failed++;
                log.warn("[DataSeeder] Failed to seed row {}/{}: {}",
                        seeded + failed, SEED_DATA.length, e.getMessage());
            }
        }

        log.info("[DataSeeder] Seeding complete: {} succeeded, {} failed",
                seeded, failed);
    }
}
