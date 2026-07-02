package com.kartikeya.airportbackend.service;

import com.kartikeya.airportbackend.dto.AirportDTOs.*;
import com.kartikeya.airportbackend.entity.PredictionHistory;
import com.kartikeya.airportbackend.repository.PredictionHistoryRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Core business logic service.
 * Orchestrates: ML service calls → persistence → response assembly.
 * Controllers stay thin — all logic lives here.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class AirportService {

    private final MlServiceClient mlServiceClient;
    private final PredictionHistoryRepository predictionHistoryRepository;

    // ── Delay Prediction ──────────────────────────────────────────────────────

    public DelayPredictionResponse predictDelay(DelayPredictionRequest request) {
        log.info("Processing delay prediction for month={}, year={}",
                request.getMonth().intValue(), request.getYear().intValue());

        // 1. Call ML service
        Map<String, Object> mlResponse = mlServiceClient.predictDelay(request);

        // 2. Extract values safely
        Integer prediction   = (Integer) mlResponse.get("high_delay_prediction");
        Double  probability  = ((Number) mlResponse.get("high_delay_probability")).doubleValue();
        String  status       = (String)  mlResponse.get("status");
        String  modelVersion = (String)  mlResponse.get("model_version");

        // 3. Persist to history
        PredictionHistory history = PredictionHistory.builder()
                .year(request.getYear().intValue())
                .month(request.getMonth().intValue())
                .arrFlights(request.getArrFlights())
                .isSummer(request.getIsSummer())
                .isWinterHoliday(request.getIsWinterHoliday())
                .yearsSince2013(request.getYearsSince2013())
                .airportAvgDelayRate(request.getAirportAvgDelayRate())
                .carrierAvgDelayRate(request.getCarrierAvgDelayRate())
                .highDelayPrediction(prediction)
                .highDelayProbability(probability)
                .status(status)
                .modelVersion(modelVersion != null ? modelVersion : "v1")
                .build();

        PredictionHistory saved = predictionHistoryRepository.save(history);
        log.info("Prediction saved to history with id={}", saved.getId());

        // 4. Build and return response
        return DelayPredictionResponse.builder()
                .highDelayPrediction(prediction)
                .highDelayProbability(probability)
                .status(status)
                .modelVersion(modelVersion)
                .predictedAt(LocalDateTime.now())
                .historyId(saved.getId())
                .build();
    }

    // ── Traffic Forecasting ───────────────────────────────────────────────────

    @SuppressWarnings("unchecked")
    public TrafficForecastResponse forecastTraffic(int days) {
        log.info("Processing traffic forecast for {} days", days);

        Map<String, Object> mlResponse = mlServiceClient.forecastTraffic(days);

        List<Map<String, Object>> rawForecast =
                (List<Map<String, Object>>) mlResponse.get("forecast");

        List<TrafficForecastPoint> forecastPoints = rawForecast.stream()
                .map(point -> TrafficForecastPoint.builder()
                        .date((String) point.get("date"))
                        .predictedFootfall(((Number) point.get("predicted_footfall")).intValue())
                        .lowerBound(((Number) point.get("lower_bound")).intValue())
                        .upperBound(((Number) point.get("upper_bound")).intValue())
                        .build())
                .collect(Collectors.toList());

        return TrafficForecastResponse.builder()
                .forecastDays(((Number) mlResponse.get("forecast_days")).intValue())
                .forecastFrom((String) mlResponse.get("forecast_from"))
                .forecastTo((String) mlResponse.get("forecast_to"))
                .modelMae(((Number) mlResponse.get("model_mae")).doubleValue())
                .modelMapePct(((Number) mlResponse.get("model_mape_pct")).doubleValue())
                .forecast(forecastPoints)
                .build();
    }

    // ── History & Dashboard ───────────────────────────────────────────────────

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
