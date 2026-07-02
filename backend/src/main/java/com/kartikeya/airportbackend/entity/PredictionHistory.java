package com.kartikeya.airportbackend.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Stores every delay prediction made via the backend API.
 * Enables the dashboard to show prediction history and trends over time.
 * Maps to the PREDICTION_HISTORY table in H2 (dev) or PostgreSQL (prod).
 */
@Entity
@Table(name = "prediction_history")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PredictionHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Input features
    @Column(name = "flight_month", nullable = false)
    private Integer month;

    @Column(name = "flight_year", nullable = false)
    private Integer year;

    @Column(nullable = false)
    private Double arrFlights;

    @Column(nullable = false)
    private Double isSummer;

    @Column(nullable = false)
    private Double isWinterHoliday;

    @Column(name = "years_since_2013", nullable = false)
    private Double yearsSince2013;

    @Column(nullable = false)
    private Double airportAvgDelayRate;

    @Column(nullable = false)
    private Double carrierAvgDelayRate;

    // Prediction outputs
    @Column(nullable = false)
    private Integer highDelayPrediction;

    @Column(nullable = false)
    private Double highDelayProbability;

    @Column(nullable = false)
    private String status;

    @Column(nullable = false)
    private String modelVersion;

    // Metadata
    @Column(nullable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
