package com.kartikeya.airportbackend.controller;

import com.kartikeya.airportbackend.dto.AirportDTOs.*;
import com.kartikeya.airportbackend.service.AirportService;
import com.kartikeya.airportbackend.service.MlServiceClient;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * Main REST controller for the Airport Operations backend.
 *
 * Endpoints:
 *   GET  /api/health                → service + ML service health check
 *   POST /api/predict/delay         → delay risk prediction (saved to DB)
 *   GET  /api/forecast/traffic      → passenger footfall forecast
 *   GET  /api/history               → last 20 predictions
 *   GET  /api/history/alerts        → high-risk predictions only
 *   GET  /api/dashboard/summary     → aggregated dashboard stats
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
@Validated
@CrossOrigin(origins = "*")  // Allow React dashboard to call this API
public class AirportController {

    private final AirportService airportService;
    private final MlServiceClient mlServiceClient;

    // ── Health ────────────────────────────────────────────────────────────────

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        boolean mlHealthy = mlServiceClient.isHealthy();
        Map<String, Object> response = Map.of(
                "status",          mlHealthy ? "healthy" : "degraded",
                "backend",         "UP",
                "ml_service",      mlHealthy ? "UP" : "DOWN",
                "timestamp",       LocalDateTime.now().toString()
        );
        return ResponseEntity.ok(response);
    }

    // ── Delay Prediction ──────────────────────────────────────────────────────

    @PostMapping("/predict/delay")
    public ResponseEntity<DelayPredictionResponse> predictDelay(
            @Valid @RequestBody DelayPredictionRequest request) {
        log.info("POST /api/predict/delay - month={}, year={}",
                request.getMonth().intValue(), request.getYear().intValue());
        DelayPredictionResponse response = airportService.predictDelay(request);
        return ResponseEntity.ok(response);
    }

    // ── Traffic Forecasting ───────────────────────────────────────────────────

    @GetMapping("/forecast/traffic")
    public ResponseEntity<TrafficForecastResponse> forecastTraffic(
            @RequestParam(defaultValue = "30")
            @Min(value = 1, message = "days must be >= 1")
            @Max(value = 365, message = "days must be <= 365")
            int days) {
        log.info("GET /api/forecast/traffic?days={}", days);
        TrafficForecastResponse response = airportService.forecastTraffic(days);
        return ResponseEntity.ok(response);
    }

    // ── History & Alerts ──────────────────────────────────────────────────────

    @GetMapping("/history")
    public ResponseEntity<List<PredictionHistoryItem>> getHistory() {
        log.info("GET /api/history");
        return ResponseEntity.ok(airportService.getRecentHistory());
    }

    @GetMapping("/history/alerts")
    public ResponseEntity<List<PredictionHistoryItem>> getAlerts() {
        log.info("GET /api/history/alerts");
        return ResponseEntity.ok(airportService.getHighRiskPredictions());
    }

    // ── Dashboard ─────────────────────────────────────────────────────────────

    @GetMapping("/dashboard/summary")
    public ResponseEntity<DashboardSummary> getDashboardSummary() {
        log.info("GET /api/dashboard/summary");
        return ResponseEntity.ok(airportService.getDashboardSummary());
    }
}
