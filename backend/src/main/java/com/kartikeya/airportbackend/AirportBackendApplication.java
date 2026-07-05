package com.kartikeya.airportbackend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Airport Operations Predictive Analytics — Spring Boot Backend
 *
 * @EnableScheduling activates the automated job scheduler (OperationsScheduler)
 * which runs daily forecasts, risk scans, and continuous monitoring without
 * any human intervention.
 */
@SpringBootApplication
@EnableScheduling
public class AirportBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(AirportBackendApplication.class, args);
    }
}
