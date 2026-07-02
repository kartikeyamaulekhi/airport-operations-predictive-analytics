package com.kartikeya.airportbackend.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Data Transfer Objects for the Airport Backend API.
 * Kept in one file for clarity — split into separate files if this grows.
 */
public class AirportDTOs {

    // ── Delay Prediction Request ──────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DelayPredictionRequest {

        @NotNull(message = "year is required")
        @Min(value = 2013, message = "year must be >= 2013")
        @Max(value = 2030, message = "year must be <= 2030")
        private Double year;

        @NotNull(message = "month is required")
        @Min(value = 1, message = "month must be between 1 and 12")
        @Max(value = 12, message = "month must be between 1 and 12")
        private Double month;

        @NotNull(message = "arr_flights is required")
        @Min(value = 1, message = "arr_flights must be >= 1")
        private Double arrFlights;

        @NotNull(message = "is_summer is required")
        @Min(value = 0) @Max(value = 1)
        private Double isSummer;

        @NotNull(message = "is_winter_holiday is required")
        @Min(value = 0) @Max(value = 1)
        private Double isWinterHoliday;

        @NotNull(message = "years_since_2013 is required")
        @Min(value = 0)
        private Double yearsSince2013;

        @NotNull(message = "airport_avg_delay_rate is required")
        @DecimalMin(value = "0.0") @DecimalMax(value = "1.0")
        private Double airportAvgDelayRate;

        @NotNull(message = "carrier_avg_delay_rate is required")
        @DecimalMin(value = "0.0") @DecimalMax(value = "1.0")
        private Double carrierAvgDelayRate;
    }

    // ── Delay Prediction Response ─────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DelayPredictionResponse {
        private Integer highDelayPrediction;
        private Double highDelayProbability;
        private String status;
        private String modelVersion;
        private LocalDateTime predictedAt;
        private Long historyId;
    }

    // ── Traffic Forecast Point ────────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TrafficForecastPoint {
        private String date;
        private Integer predictedFootfall;
        private Integer lowerBound;
        private Integer upperBound;
    }

    // ── Traffic Forecast Response ─────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TrafficForecastResponse {
        private Integer forecastDays;
        private String forecastFrom;
        private String forecastTo;
        private Double modelMae;
        private Double modelMapePct;
        private List<TrafficForecastPoint> forecast;
    }

    // ── Prediction History Item ───────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class PredictionHistoryItem {
        private Long id;
        private Integer highDelayPrediction;
        private Double highDelayProbability;
        private String status;
        private Integer month;
        private Integer year;
        private LocalDateTime createdAt;
    }

    // ── Dashboard Summary ─────────────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DashboardSummary {
        private Long totalPredictions;
        private Long highRiskCount;
        private Long nominalCount;
        private Double highRiskPercentage;
        private List<PredictionHistoryItem> recentPredictions;
    }

    // ── API Error Response ────────────────────────────────────────────────────
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ErrorResponse {
        private String error;
        private String message;
        private Integer status;
        private LocalDateTime timestamp;
    }
}
