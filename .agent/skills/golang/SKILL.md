---
name: golang
description: Best practices for Golang backend development. Sử dụng khi cần viết, review, hoặc tối ưu Go code. Bao gồm Clean Architecture (Handler→Service→Repository), error handling, concurrency, middleware, database, và testing patterns.
---

# Golang Skill

## 1. Project Layout
*   Tuân thủ **Clean Architecture**:
    *   `handler`: HTTP/gRPC Handlers (input validation, response formatting).
    *   `service`: Business Logic (core operations).
    *   `repository`: Data Access Layer (SQL queries, external API calls).
    *   `model`: Domain models & DTOs.
    *   `config`: Configuration loading (`viper`).
    *   `pkg`: Library code (logger, utils).

## 2. Error Handling & Logging
*   **Error Wrapping**:
    ```go
    if err != nil {
        return fmt.Errorf("failed to process order: %w", err)
    }
    ```
*   **Structured Logging**: Sử dụng `slog` (Go 1.21+) hoặc `zap`.
    ```go
    slog.Error("database query failed", "error", err, "query", sqlQuery)
    ```
*   Không log sensitive info (password, token).

## 3. Middleware Pattern
*   Chain các middleware cho: Auth, Logging, CORS, Panic Recovery.
    ```go
    func LoggingMiddleware(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            next.ServeHTTP(w, r)
            slog.Info("request handled", "method", r.Method, "duration", time.Since(start))
        })
    }
    ```

## 4. Configuration
*   Sử dụng **Viper** để load config từ file (yaml/json) và environment variables.
*   Hot-reload config nếu cần thiết (dùng `viper.WatchConfig()`).

## 5. Concurrency
*   **Context Propagation**: Luôn truyền `ctx` vào hàm database/network call để support cancellation/timeout.
*   **Worker Pool**: Giới hạn số lượng goroutines khi xử lý batch job lớn.
*   **Race Detection**: CI pipeline bắt buộc chạy `go test -race`.

## 6. Testing
*   **Table-Driven Tests**: Pattern chuẩn cho unit test.
*   **Mocking**: Sử dụng `mockery` hoặc `gomock` để gen mocks cho interface Service/Repository.
*   **Integration Test**: Sử dụng Docker container (Testcontainers-go) để spin up DB thật.

## 7. Database (SQL)
*   Sử dụng `sqlx` hoặc `gorm`.
*   **Transactions**:
    ```go
    tx := db.Begin()
    defer func() {
        if r := recover(); r != nil { tx.Rollback() }
    }()
    // ... operations ...
    tx.Commit()
    ```
