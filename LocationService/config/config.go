package config

import (
	"os"
	"time"
)

type Config struct {
	GRPCPort            string
	DatabaseURL         string
	VehicleAPIURL       string
	VehicleAPIToken     string
	VehiclePollInterval time.Duration
}

func Load() *Config {
	interval, err := time.ParseDuration(getEnv("VEHICLE_POLL_INTERVAL", "1s"))
	if err != nil {
		interval = 1 * time.Second
	}
	return &Config{
		GRPCPort:            getEnv("GRPC_PORT", "50051"),
		DatabaseURL:         getEnv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/locationservice"),
		VehicleAPIURL:       getEnv("VEHICLE_API_URL", "http://25.1.1.217:80/api/mobject/lastData"),
		VehicleAPIToken:     getEnv("VEHICLE_API_TOKEN", "6bq6kimsmhniuothjbkai715n2"),
		VehiclePollInterval: interval,
	}
}

func getEnv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
