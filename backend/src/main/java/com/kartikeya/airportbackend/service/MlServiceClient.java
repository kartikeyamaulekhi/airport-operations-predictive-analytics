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
import java.util.Map;

/**
 * Client service that communicates with the Python FastAPI ML microservice.
 * All ML inference is delegated here — keeping controllers clean and making
 * the ML service easy to swap or mock in tests.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class MlServiceClient {

    private final RestTemplate restTemplate;

    @Value("${ml.service.url}")
    private String mlServiceUrl;

    @Value("${ml.service.forecast.days:30}")
    private int forecastDays;

    /**
     * Calls POST /predict on the FastAPI ML service.
     * Maps the backend request DTO to the exact field names FastAPI expects.
     */
    public Map<String, Object> predictDelay(DelayPredictionRequest request) {
        String url = mlServiceUrl + "/predict";

        // Build request body matching FastAPI's FlightFeatures schema exactly
        Map<String, Object> mlRequest = new HashMap<>();
        mlRequest.put("year",                    request.getYear());
        mlRequest.put("month",                   request.getMonth());
        mlRequest.put("arr_flights",             request.getArrFlights());
        mlRequest.put("is_summer",               request.getIsSummer());
        mlRequest.put("is_winter_holiday",       request.getIsWinterHoliday());
        mlRequest.put("years_since_2013",        request.getYearsSince2013());
        mlRequest.put("airport_avg_delay_rate",  request.getAirportAvgDelayRate());
        mlRequest.put("carrier_avg_delay_rate",  request.getCarrierAvgDelayRate());

        log.info("Calling ML service: POST {}", url);

        try {
            @SuppressWarnings("unchecked")
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    url, mlRequest, Map.class);
            log.info("ML service responded: {}", response.getStatusCode());
            return response.getBody();
        } catch (ResourceAccessException e) {
            log.error("ML service unreachable at {}: {}", url, e.getMessage());
            throw new RuntimeException(
                    "ML service is currently unavailable. Please try again later.");
        } catch (Exception e) {
            log.error("ML service call failed: {}", e.getMessage());
            throw new RuntimeException("Prediction failed: " + e.getMessage());
        }
    }

    /**
     * Calls GET /forecast/traffic on the FastAPI ML service.
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> forecastTraffic(int days) {
        String url = mlServiceUrl + "/forecast/traffic?days=" + days;
        log.info("Calling ML service: GET {}", url);

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            log.info("ML service forecast responded: {}", response.getStatusCode());
            return response.getBody();
        } catch (ResourceAccessException e) {
            log.error("ML service unreachable at {}: {}", url, e.getMessage());
            throw new RuntimeException(
                    "ML service is currently unavailable. Please try again later.");
        } catch (Exception e) {
            log.error("ML service forecast failed: {}", e.getMessage());
            throw new RuntimeException("Forecasting failed: " + e.getMessage());
        }
    }

    /**
     * Checks if the ML service is alive — used by the /health endpoint.
     */
    public boolean isHealthy() {
        try {
            String url = mlServiceUrl + "/health";
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("ML service health check failed: {}", e.getMessage());
            return false;
        }
    }
}
