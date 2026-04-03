package postgres

import (
	"context"
	"fmt"
	"LocationService/internal/repository"
	"LocationService/models"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type locationRepo struct {
	db *pgxpool.Pool
}

func NewLocationRepo(db *pgxpool.Pool) repository.LocationRepo {
	return &locationRepo{db: db}
}

func (r *locationRepo) Save(ctx context.Context, loc *models.Location) error {
	_, err := r.db.Exec(ctx,
		`INSERT INTO locations (pinfl_hash, latitude, longitude, accuracy, recorded_at)
		 VALUES ($1, $2, $3, $4, to_timestamp($5::bigint/1000.0))`,
		loc.PinflHash, loc.Latitude, loc.Longitude, loc.Accuracy, loc.RecordedAt.UnixMilli(),
	)
	if err != nil {
		return fmt.Errorf("save location: %w", err)
	}
	return nil
}

func (r *locationRepo) GetLatestByPinfl(ctx context.Context, pinflHash string) (*models.Location, error) {
	loc := &models.Location{}
	err := r.db.QueryRow(ctx,
		`SELECT id, pinfl_hash, latitude, longitude, accuracy, recorded_at
		 FROM locations WHERE pinfl_hash=$1 ORDER BY recorded_at DESC LIMIT 1`,
		pinflHash,
	).Scan(&loc.ID, &loc.PinflHash, &loc.Latitude, &loc.Longitude, &loc.Accuracy, &loc.RecordedAt)
	if err != nil {
		if err == pgx.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("get latest location: %w", err)
	}
	return loc, nil
}

func (r *locationRepo) HasPointVisit(ctx context.Context, pinflHash string, pointID, dutyID int32) (bool, error) {
	var count int
	err := r.db.QueryRow(ctx,
		`SELECT COUNT(*) FROM point_visits WHERE pinfl_hash=$1 AND point_id=$2 AND duty_id=$3`,
		pinflHash, pointID, dutyID,
	).Scan(&count)
	if err != nil {
		return false, fmt.Errorf("has point visit: %w", err)
	}
	return count > 0, nil
}

func (r *locationRepo) SavePointVisit(ctx context.Context, pinflHash string, pointID, dutyID int32) error {
	_, err := r.db.Exec(ctx,
		`INSERT INTO point_visits (pinfl_hash, point_id, duty_id) VALUES ($1, $2, $3)
		 ON CONFLICT (pinfl_hash, point_id, duty_id) DO NOTHING`,
		pinflHash, pointID, dutyID,
	)
	if err != nil {
		return fmt.Errorf("save point visit: %w", err)
	}
	return nil
}

func (r *locationRepo) SaveVehicleLocation(ctx context.Context, vl *models.VehicleLocation) error {
	_, err := r.db.Exec(ctx,
		`INSERT INTO vehicle_locations (plate_number, latitude, longitude, speed, engine_on, tp_timestamp)
		 VALUES ($1, $2, $3, $4, $5, $6)`,
		vl.PlateNumber, vl.Latitude, vl.Longitude, vl.Speed, vl.EngineOn, vl.TpTimestamp,
	)
	if err != nil {
		return fmt.Errorf("save vehicle location: %w", err)
	}
	return nil
}

func (r *locationRepo) GetLatestVehicleLocation(ctx context.Context, plateNumber string) (*models.VehicleLocation, error) {
	vl := &models.VehicleLocation{}
	err := r.db.QueryRow(ctx,
		`SELECT id, plate_number, latitude, longitude, speed, engine_on, tp_timestamp, recorded_at
		 FROM vehicle_locations WHERE plate_number=$1 ORDER BY recorded_at DESC LIMIT 1`,
		plateNumber,
	).Scan(&vl.ID, &vl.PlateNumber, &vl.Latitude, &vl.Longitude, &vl.Speed, &vl.EngineOn, &vl.TpTimestamp, &vl.RecordedAt)
	if err != nil {
		if err == pgx.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("get latest vehicle location: %w", err)
	}
	return vl, nil
}
