# Stage 1: Build with Maven
FROM maven:3.9.6-eclipse-temurin-17 AS builder

WORKDIR /build

# Copy pom.xml first for dependency caching
COPY pom.xml .
RUN mvn dependency:go-offline -q

# Copy source and build
COPY src/ ./src/
RUN mvn clean package -DskipTests -q

# Stage 2: Production image
FROM eclipse-temurin:17-jre-jammy AS production

ENV APP_ENV=production \
    SERVER_PORT=8080

WORKDIR /app

# Copy the built jar
COPY --from=builder /build/target/*.jar app.jar

# Non-root user for security
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD java -cp app.jar org.springframework.boot.loader.launch.PropertiesLauncher 2>/dev/null || \
    wget -q --spider http://localhost:8080/actuator/health || exit 1

CMD ["java", "-Xmx256m", "-Xms128m", \
     "-Dserver.port=${PORT:-8080}", \
     "-jar", "app.jar"]
