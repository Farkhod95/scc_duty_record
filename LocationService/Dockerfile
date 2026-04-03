# ── Build stage ──────────────────────────────────────────────
FROM golang:1.26-alpine AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -trimpath -o location-service ./cmd/main.go

# ── Run stage ─────────────────────────────────────────────────
FROM alpine:3.19

RUN apk add --no-cache tzdata ca-certificates
ENV TZ=Asia/Tashkent

WORKDIR /app

COPY --from=builder /app/location-service .

EXPOSE 50051

ENTRYPOINT ["./location-service"]
