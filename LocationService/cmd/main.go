package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"LocationService/config"
	"LocationService/internal/handler"
	"LocationService/internal/repository/external"
	"LocationService/internal/repository/postgres"
	"LocationService/internal/service"
	"LocationService/proto"

	pgxpool "github.com/jackc/pgx/v5/pgxpool"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

func main() {
	cfg := config.Load()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// DB ulanish
	pool, err := pgxpool.New(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("db connect: %v", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("db ping: %v", err)
	}
	log.Println("PostgreSQL ga ulandi")

	// Repository
	paligonRepo := postgres.NewPaligonRepo(pool)
	pointRepo   := postgres.NewPointRepo(pool)
	dutyRepo    := postgres.NewDutyRepo(pool)
	locationRepo := postgres.NewLocationRepo(pool)
	vehicleTracker := external.NewVehicleTracker(cfg.VehicleAPIURL, cfg.VehicleAPIToken)

	// Service
	svc := service.NewLocationService(
		paligonRepo,
		pointRepo,
		dutyRepo,
		locationRepo,
		vehicleTracker,
		cfg.VehiclePollInterval,
	)

	// Vehicle poller (fon)
	go svc.RunVehiclePoller(ctx)
	log.Printf("Vehicle poller ishga tushdi (interval: %s)", cfg.VehiclePollInterval)

	// gRPC server
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", cfg.GRPCPort))
	if err != nil {
		log.Fatalf("listen: %v", err)
	}

	grpcServer := grpc.NewServer()
	proto.RegisterLocationServiceServer(grpcServer, handler.NewLocationHandler(svc))
	reflection.Register(grpcServer)

	// Graceful shutdown
	go func() {
		quit := make(chan os.Signal, 1)
		signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
		<-quit
		log.Println("Server to'xtatilmoqda...")
		cancel()
		grpcServer.GracefulStop()
	}()

	log.Printf("gRPC server :%s portda ishga tushdi", cfg.GRPCPort)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("serve: %v", err)
	}
}
