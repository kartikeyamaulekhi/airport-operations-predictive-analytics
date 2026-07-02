package com.kartikeya.airportbackend.service;

import com.kartikeya.airportbackend.dto.AirportDTOs.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class MlServiceClient {

    private final RestTemplate restTemplate;

    @Value("${ml.service.url}")
    private String mlServiceUrl;

    @Value("${ml.service.forecast.days:30}")
    private int forecastDays;

    private static final int MAX_RETRIES = 2;
    private static final long BACKOFF_DELAY_MS = 2000;

    // --- Strongly Typed Response Records for Schema Stability ---
    public record DelayPredictionResponse(
            int high_delay_prediction,
            double high_delay_probability,
            String status,
            String model_version
    ) {}

    public record TrafficForecastPoint(
            String date,
            int predicted_footfall,
            int lower_bound,
            int upper_bound
    ) {}

    public record TrafficForecastResponse(
            int forecast_days,
            String forecast_from,
            String forecast_to,
            double model_mae,
            double model_mape_pct,
            List<TrafficForecastPoint> forecast
    ) {}

    /**
     * Calls POST /predict on the FastAPI ML service with explicit type safety and retry logic.
     */
    public DelayPredictionResponse predictDelay(DelayPredictionRequest request) {
        String requestId = generateShortId();
        String url = mlServiceUrl + "/predict";
        Map<String, Object> mlRequest = buildDelayRequest(request);

        log.info("[{}] Calling ML service: POST {}", requestId, url);

        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                ResponseEntity<DelayPredictionResponse> response = restTemplate.postForEntity(
                        url, mlRequest, DelayPredictionResponse.class);

                log.info("[{}] ML service responded: {} (attempt {})",
                        requestId, response.getStatusCode(), attempt);
                return response.getBody();

            } catch (ResourceAccessException e) {
                handleRetryBackoff(requestId, attempt, e);
            } catch (Exception e) {
                log.error("[{}] ML service call failed due to unexpected error: {}", requestId, e.getMessage());
                throw new RuntimeException("Prediction failed: " + e.getMessage(), e);
            }
        }
        throw new RuntimeException("Prediction failed after maximum retries");
    }

    /**
     * Calls GET /forecast/traffic with explicit JSON mapping matching snake_case models.
     */
    public TrafficForecastResponse forecastTraffic(int days) {
        String requestId = generateShortId();
        // Ensure mlServiceUrl matches internal paths (e.g. http://localhost:8080/forecast/traffic)
        String url = String.format("%s/forecast/traffic?days=%d", mlServiceUrl, days);

        log.info("[{}] Calling ML service: GET {}", requestId, url);

        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                ResponseEntity<TrafficForecastResponse> response = restTemplate.getForEntity(
                        url, TrafficForecastResponse.class);

                log.info("[{}] ML forecast responded: {} (attempt {})",
                        requestId, response.getStatusCode(), attempt);
                return response.getBody();

            } catch (ResourceAccessException e) {
                handleRetryBackoff(requestId, attempt, e);
            } catch (Exception e) {
                log.error("[{}] ML forecast failed due to unexpected error: {}", requestId, e.getMessage());
                throw new RuntimeException("Forecasting failed: " + e.getMessage(), e);
            }
        }
        throw new RuntimeException("Forecasting failed after maximum retries");
    }

    /**
     * Checks ML service health — used by /api/health endpoint.
     */
    public boolean isHealthy() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                    mlServiceUrl + "/health", Map.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("ML service health check failed: {}", e.getMessage());
            return false;
        }
    }

    private Map<String, Object> buildDelayRequest(DelayPredictionRequest request) {
        Map<String, Object> mlRequest = new HashMap<>();
        mlRequest.put("year",                   request.getYear());
        mlRequest.put("month",                  request.getMonth());
        mlRequest.put("arr_flights",            request.getArrFlights());
        mlRequest.put("is_summer",              request.getIsSummer());
        mlRequest.put("is_winter_holiday",      request.getIsWinterHoliday());
        mlRequest.put("years_since_2013",       request.getYearsSince2013());
        mlRequest.put("airport_avg_delay_rate", request.getAirportAvgDelayRate());
        mlRequest.put("carrier_avg_delay_rate", request.getCarrierAvgDelayRate());
        return mlRequest;
    }

    private String generateShortId() {
        return UUID.randomUUID().toString().substring(0, 8);
    }

    private void handleRetryBackoff(String requestId, int attempt, ResourceAccessException e) {
        log.warn("[{}] ML service timeout on attempt {}/{}: {}", requestId, attempt, MAX_RETRIES, e.getMessage());
        if (attempt == MAX_RETRIES) {
            log.error("[{}] ML service unreachable after {} attempts", requestId, MAX_RETRIES);
            throw new RuntimeException("ML service is currently unavailable. Cold start in progress — please retry in 30 seconds.", e);
        }
        try {
            Thread.sleep(BACKOFF_DELAY_MS);
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Retry wait pattern was interrupted interrupted", ie);
        }
    }
}