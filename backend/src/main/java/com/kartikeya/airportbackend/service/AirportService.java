package com.kartikeya.airportbackend.service;

import com.kartikeya.airportbackend.dto.AirportDTOs.*;
import com.kartikeya.airportbackend.entity.PredictionHistory;
import com.kartikeya.airportbackend.repository.PredictionHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Core business logic service.
 * Orchestrates: ML service calls ? persistence ? response assembly.
 * Controllers stay thin — all logic lives here.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AirportService {

    private final MlServiceClient mlServiceClient;
    private final PredictionHistoryRepository predictionHistoryRepository;

    // -- Delay Prediction ------------------------------------------------------

    public DelayPredictionResponse predictDelay(DelayPredictionRequest request) {
        log.info("Processing delay prediction for month={}, year={}",
                request.getMonth().intValue(), request.getYear().intValue());

        // 1. Call ML service (returns strongly typed Record)
        MlServiceClient.DelayPredictionResponse mlResponse = mlServiceClient.predictDelay(request);

        // 2. Persist to history using type-safe Record getters
        PredictionHistory history = PredictionHistory.builder()
                .year(request.getYear().intValue())
                .month(request.getMonth().intValue())
                .arrFlights(request.getArrFlights())
                .isSummer(request.getIsSummer())
                .isWinterHoliday(request.getIsWinterHoliday())
                .yearsSince2013(request.getYearsSince2013())
                .airportAvgDelayRate(request.getAirportAvgDelayRate())
                .carrierAvgDelayRate(request.getCarrierAvgDelayRate())
                .highDelayPrediction(mlResponse.high_delay_prediction())
                .highDelayProbability(mlResponse.high_delay_probability())
                .status(mlResponse.status())
                .modelVersion(mlResponse.model_version() != null ? mlResponse.model_version() : "v1")
                .build();

        PredictionHistory saved = predictionHistoryRepository.save(history);
        log.info("Prediction saved to history with id={}", saved.getId());

        // 3. Build and return response
        return DelayPredictionResponse.builder()
                .highDelayPrediction(mlResponse.high_delay_prediction())
                .highDelayProbability(mlResponse.high_delay_probability())
                .status(mlResponse.status())
                .modelVersion(mlResponse.model_version())
                .predictedAt(LocalDateTime.now())
                .historyId(saved.getId())
                .build();
    }

    // -- Traffic Forecasting ---------------------------------------------------

    public TrafficForecastResponse forecastTraffic(int days) {
        log.info("Processing traffic forecast for {} days", days);

        // 1. Call ML service (returns strongly typed Record)
        MlServiceClient.TrafficForecastResponse mlResponse = mlServiceClient.forecastTraffic(days);

        // 2. Map the data cleanly without unsafe Map casting loops
        List<TrafficForecastPoint> forecastPoints = mlResponse.forecast().stream()
                .map(point -> TrafficForecastPoint.builder()
                        .date(point.date())
                        .predictedFootfall(point.predicted_footfall())
                        .lowerBound(point.lower_bound())
                        .upperBound(point.upper_bound())
                        .build())
                .collect(Collectors.toList());

        return TrafficForecastResponse.builder()
                .forecastDays(mlResponse.forecast_days())
                .forecastFrom(mlResponse.forecast_from())
                .forecastTo(mlResponse.forecast_to())
                .modelMae(mlResponse.model_mae())
                .modelMapePct(mlResponse.model_mape_pct())
                .forecast(forecastPoints)
                .build();
    }

    // -- History & Dashboard ---------------------------------------------------

    public List<PredictionHistoryItem> getRecentHistory() {
        return predictionHistoryRepository.findTop20ByOrderByCreatedAtDesc()
                .stream()
                .map(h -> PredictionHistoryItem.builder()
                        .id(h.getId())
                        .highDelayPrediction(h.getHighDelayPrediction())
                        .highDelayProbability(h.getHighDelayProbability())
                        .status(h.getStatus())
                        .month(h.getMonth())
                        .year(h.getYear())
                        .createdAt(h.getCreatedAt())
                        .build())
                .collect(Collectors.toList());
    }

    public List<PredictionHistoryItem> getHighRiskPredictions() {
        return predictionHistoryRepository
                .findByHighDelayPredictionOrderByCreatedAtDesc(1)
                .stream()
                .map(h -> PredictionHistoryItem.builder()
                        .id(h.getId())
                        .highDelayPrediction(h.getHighDelayPrediction())
                        .highDelayProbability(h.getHighDelayProbability())
                        .status(h.getStatus())
                        .month(h.getMonth())
                        .year(h.getYear())
                        .createdAt(h.getCreatedAt())
                        .build())
                .collect(Collectors.toList());
    }

    public DashboardSummary getDashboardSummary() {
        long total    = predictionHistoryRepository.count();
        long highRisk = predictionHistoryRepository
                .findByHighDelayPredictionOrderByCreatedAtDesc(1).size();
        long nominal  = total - highRisk;
        double riskPct = total > 0 ? (highRisk * 100.0 / total) : 0.0;

        return DashboardSummary.builder()
                .totalPredictions(total)
                .highRiskCount(highRisk)
                .nominalCount(nominal)
                .highRiskPercentage(Math.round(riskPct * 100.0) / 100.0)
                .recentPredictions(getRecentHistory())
                .build();
    }
}
