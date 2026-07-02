package com.kartikeya.airportbackend.exception;

import com.kartikeya.airportbackend.dto.AirportDTOs.ErrorResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.LocalDateTime;
import java.util.stream.Collectors;

/**
 * Catches all unhandled exceptions and returns clean, consistent
 * JSON error responses instead of Spring's default HTML error pages.
 * This is what makes an API feel professional.
 */
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    // Validation errors (e.g. missing fields, out-of-range values)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationErrors(
            MethodArgumentNotValidException ex) {

        String message = ex.getBindingResult().getFieldErrors()
                .stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.joining(", "));

        log.warn("Validation failed: {}", message);

        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ErrorResponse.builder()
                        .error("Validation Failed")
                        .message(message)
                        .status(400)
                        .timestamp(LocalDateTime.now())
                        .build());
    }

    // ML service unavailable
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ErrorResponse> handleRuntimeException(RuntimeException ex) {
        log.error("Runtime error: {}", ex.getMessage());

        boolean isMlError = ex.getMessage() != null &&
                (ex.getMessage().contains("ML service") ||
                 ex.getMessage().contains("unavailable"));

        HttpStatus status = isMlError
                ? HttpStatus.SERVICE_UNAVAILABLE
                : HttpStatus.INTERNAL_SERVER_ERROR;

        return ResponseEntity
                .status(status)
                .body(ErrorResponse.builder()
                        .error(isMlError ? "ML Service Unavailable" : "Internal Server Error")
                        .message(ex.getMessage())
                        .status(status.value())
                        .timestamp(LocalDateTime.now())
                        .build());
    }

    // Catch-all
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("Unexpected error: {}", ex.getMessage(), ex);
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ErrorResponse.builder()
                        .error("Internal Server Error")
                        .message("An unexpected error occurred")
                        .status(500)
                        .timestamp(LocalDateTime.now())
                        .build());
    }
}
