package com.kartikeya.airportbackend.config;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.UUID;

@Component
@Order(1)
@Slf4j
public class RequestLoggingFilter implements Filter {

    public static final String REQUEST_ID_HEADER = "X-Request-Id";
    private static final String MDC_REQUEST_ID_KEY = "requestId";
    private static final int SHORT_ID_LENGTH = 8;

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        if (!(request instanceof HttpServletRequest httpRequest) || !(response instanceof HttpServletResponse httpResponse)) {
            chain.doFilter(request, response);
            return;
        }

        String requestId = resolveOrCreateRequestId(httpRequest);
        long startTime = System.currentTimeMillis();

        try {
            MDC.put(MDC_REQUEST_ID_KEY, requestId);
            httpResponse.setHeader(REQUEST_ID_HEADER, requestId);

            log.info("--> {} {}", httpRequest.getMethod(), httpRequest.getRequestURI());

            chain.doFilter(httpRequest, httpResponse);
        } finally {
            long duration = System.currentTimeMillis() - startTime;
            log.info("<-- {} in {}ms", httpResponse.getStatus(), duration);
            MDC.remove(MDC_REQUEST_ID_KEY);
        }
    }

    private String resolveOrCreateRequestId(HttpServletRequest request) {
        String existingId = request.getHeader(REQUEST_ID_HEADER);
        if (existingId != null && !existingId.isBlank()) {
            return existingId;
        }
        return UUID.randomUUID().toString().replace("-", "").substring(0, SHORT_ID_LENGTH);
    }
}
