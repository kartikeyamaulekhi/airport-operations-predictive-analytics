package com.kartikeya.airportbackend.scheduler;

import com.kartikeya.airportbackend.dto.AirportDTOs.*;
import com.kartikeya.airportbackend.entity.PredictionHistory;
import com.kartikeya.airportbackend.repository.PredictionHistoryRepository;
import com.kartikeya.airportbackend.service.AirportService;
import com.kartikeya.airportbackend.alert.AlertService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * OperationsScheduler — the "automated AI-driven" heart of the system.
 *
 * Runs without any human intervention:
 *   - 06:00 daily: fetches 30-day passenger forecast, logs summary
 *   - 06:05 daily: scans recent predictions for high-risk patterns, sends alerts
 *   - Every 6 hours: generates a fresh delay prediction for current month
 *     (simulates continuous monitoring across the day)
 *
 * This is what separates a "deployed ML model" from an "automated AI system."
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class OperationsScheduler {

    private final AirportService       airportService;
    private final AlertService         alertService;
    private final PredictionHistoryRepository predictionHistoryRepository;

    private static final double HIGH_RISK_THRESHOLD = 0.65;
    private static final DateTimeFormatter FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");

    // ── 1. Daily morning forecast at 06:00 ───────────────────────────────────
    @Scheduled(cron = "0 0 6 * * *")
    public void runDailyForecast() {
        log.info("=== [SCHEDULER] Daily forecast job started at {} ===",
                LocalDateTime.now().format(FMT));
        try {
            TrafficForecastResponse forecast = airportService.forecastTraffic(30);
            int totalPax = forecast.getForecast().stream()
                    .mapToInt(TrafficForecastPoint::getPredictedFootfall)
                    .sum();
            int peakDay = forecast.getForecast().stream()
                    .mapToInt(TrafficForecastPoint::getPredictedFootfall)
                    .max().orElse(0);

            log.info("[SCHEDULER] 30-day forecast complete: " +
                     "total={} passengers, peak_day={}, MAE={}",
                    totalPax, peakDay, forecast.getModelMae());

            // Alert if any day exceeds 45,000 passengers (capacity threshold)
            forecast.getForecast().stream()
                    .filter(p -> p.getPredictedFootfall() > 45000)
                    .forEach(p -> {
                        String msg = String.format(
                            "HIGH TRAFFIC ALERT: %s forecast %,d passengers " +
                            "(exceeds 45,000 capacity threshold)",
                            p.getDate(), p.getPredictedFootfall());
                        log.warn("[SCHEDULER] {}", msg);
                        alertService.sendAlert("High Traffic Day Forecast", msg);
                    });

        } catch (Exception e) {
            log.error("[SCHEDULER] Daily forecast failed: {}", e.getMessage());
        }
    }

    // ── 2. Daily risk scan at 06:05 ───────────────────────────────────────────
    @Scheduled(cron = "0 5 6 * * *")
    public void runDailyRiskScan() {
        log.info("=== [SCHEDULER] Daily risk scan started at {} ===",
                LocalDateTime.now().format(FMT));
        try {
            // Check predictions from the last 24 hours
            LocalDateTime since = LocalDateTime.now().minusHours(24);
            List<PredictionHistory> recent =
                    predictionHistoryRepository.findByCreatedAtBetweenOrderByCreatedAtDesc(
                            since, LocalDateTime.now());

            long highRiskCount = recent.stream()
                    .filter(p -> p.getHighDelayProbability() >= HIGH_RISK_THRESHOLD)
                    .count();

            log.info("[SCHEDULER] Risk scan: {} predictions in last 24h, " +
                     "{} high-risk (>= {}%)",
                    recent.size(), highRiskCount,
                    (int)(HIGH_RISK_THRESHOLD * 100));

            if (highRiskCount > 0) {
                String summary = String.format(
                    "%d high-risk delay predictions detected in the last 24 hours " +
                    "(probability >= %d%%). Immediate review recommended.",
                    highRiskCount, (int)(HIGH_RISK_THRESHOLD * 100));
                alertService.sendAlert("Daily Risk Scan: High-Risk Detections", summary);
            }

        } catch (Exception e) {
            log.error("[SCHEDULER] Daily risk scan failed: {}", e.getMessage());
        }
    }

    // ── 3. Continuous monitoring every 6 hours ────────────────────────────────
    @Scheduled(fixedDelay = 6 * 60 * 60 * 1000) // every 6 hours
    public void runContinuousMonitoring() {
        log.info("=== [SCHEDULER] Continuous monitoring run at {} ===",
                LocalDateTime.now().format(FMT));
        try {
            int currentMonth = LocalDateTime.now().getMonthValue();
            int currentYear  = LocalDateTime.now().getYear();
            boolean isSummer = currentMonth >= 6 && currentMonth <= 8;
            boolean isWinter = currentMonth == 12 || currentMonth == 1;

            DelayPredictionRequest request = DelayPredictionRequest.builder()
                    .year((double) currentYear)
                    .month((double) currentMonth)
                    .arrFlights(250.0)
                    .isSummer(isSummer ? 1.0 : 0.0)
                    .isWinterHoliday(isWinter ? 1.0 : 0.0)
                    .yearsSince2013((double)(currentYear - 2013))
                    .airportAvgDelayRate(0.183)
                    .carrierAvgDelayRate(0.165)
                    .build();

            DelayPredictionResponse result = airportService.predictDelay(request);

            log.info("[SCHEDULER] Monitoring prediction: status={}, probability={}",
                    result.getStatus(), result.getHighDelayProbability());

            // Auto-alert if high risk detected during monitoring
            if (result.getHighDelayProbability() >= HIGH_RISK_THRESHOLD) {
                String msg = String.format(
                    "AUTOMATED ALERT — Continuous monitoring detected HIGH DELAY RISK " +
                    "for %s/%d: probability=%.1f%%. " +
                    "Consider proactive gate reallocation.",
                    getMonthName(currentMonth), currentYear,
                    result.getHighDelayProbability() * 100);
                alertService.sendAlert("Automated Monitoring Alert", msg);
            }

        } catch (Exception e) {
            log.error("[SCHEDULER] Continuous monitoring failed: {}", e.getMessage());
        }
    }

    private String getMonthName(int month) {
        String[] months = {"Jan","Feb","Mar","Apr","May","Jun",
                           "Jul","Aug","Sep","Oct","Nov","Dec"};
        return months[Math.max(0, Math.min(11, month - 1))];
    }
}
