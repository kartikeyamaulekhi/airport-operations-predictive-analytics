package com.kartikeya.airportbackend.repository;

import com.kartikeya.airportbackend.entity.PredictionHistory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Spring Data JPA repository for prediction history.
 * Spring auto-generates all SQL — no boilerplate needed.
 */
@Repository
public interface PredictionHistoryRepository extends JpaRepository<PredictionHistory, Long> {

    // Find all high-risk predictions (for the dashboard alert panel)
    List<PredictionHistory> findByHighDelayPredictionOrderByCreatedAtDesc(Integer highDelayPrediction);

    // Find predictions in a time window (for trend analysis)
    List<PredictionHistory> findByCreatedAtBetweenOrderByCreatedAtDesc(
            LocalDateTime start, LocalDateTime end);

    // Count high-risk vs nominal predictions (for dashboard summary stats)
    @Query("SELECT p.status, COUNT(p) FROM PredictionHistory p GROUP BY p.status")
    List<Object[]> countByStatus();

    // Latest N predictions (for history feed on dashboard)
    List<PredictionHistory> findTop20ByOrderByCreatedAtDesc();
}
