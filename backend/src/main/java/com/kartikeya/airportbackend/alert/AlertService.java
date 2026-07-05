package com.kartikeya.airportbackend.alert;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

/**
 * AlertService — sends automated email alerts when the system detects
 * high-risk conditions without any human triggering the action.
 *
 * Uses Spring Mail with Gmail SMTP. Configure via environment variables:
 *   ALERT_EMAIL_TO    — recipient email
 *   ALERT_EMAIL_FROM  — sender Gmail address
 *   MAIL_PASSWORD     — Gmail App Password (not your regular password)
 *
 * If email is not configured, alerts are logged only (graceful degradation).
 * This ensures the system works even without email config — never crashes.
 */
@Service
@Slf4j
public class AlertService {

    private final JavaMailSender mailSender;

    @Value("${alert.email.to:}")
    private String alertEmailTo;

    @Value("${alert.email.from:}")
    private String alertEmailFrom;

    @Value("${alert.email.enabled:false}")
    private boolean emailEnabled;

    public AlertService(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    /**
     * Sends an alert. If email is configured, sends email.
     * Always logs the alert regardless — so it appears in Render logs.
     */
    public void sendAlert(String subject, String message) {
        // Always log — visible in Render dashboard logs
        log.warn("🚨 ALERT [{}]: {}", subject, message);

        if (!emailEnabled || alertEmailTo.isBlank() || alertEmailFrom.isBlank()) {
            log.info("[AlertService] Email not configured — alert logged only. " +
                     "Set ALERT_EMAIL_TO, ALERT_EMAIL_FROM, MAIL_PASSWORD to enable email alerts.");
            return;
        }

        try {
            SimpleMailMessage mail = new SimpleMailMessage();
            mail.setFrom(alertEmailFrom);
            mail.setTo(alertEmailTo);
            mail.setSubject("[Airport Ops] " + subject);
            mail.setText(
                "Airport Operations Predictive Analytics — Automated Alert\n\n" +
                subject + "\n\n" +
                message + "\n\n" +
                "---\n" +
                "This alert was generated automatically by the ML monitoring system.\n" +
                "No human action triggered this alert.\n" +
                "Dashboard: https://airport-operations-predictive-analytics-pydn9pjwv-kartikeya5.vercel.app"
            );
            mailSender.send(mail);
            log.info("[AlertService] Email alert sent to {}", alertEmailTo);
        } catch (Exception e) {
            log.error("[AlertService] Failed to send email alert: {}", e.getMessage());
            // Never let email failure crash the scheduler
        }
    }
}
