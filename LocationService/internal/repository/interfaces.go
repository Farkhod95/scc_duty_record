package repository

import (
	"context"
	"LocationService/models"
)

type PaligonRepo interface {
	Create(ctx context.Context, p *models.Paligon) (int32, error)
	Update(ctx context.Context, p *models.Paligon) error
	Delete(ctx context.Context, id int32) error
	List(ctx context.Context, filter PaligonFilter) ([]*models.Paligon, error)
	GetByID(ctx context.Context, id int32) (*models.Paligon, error)
}

type PaligonFilter struct {
	ID         *int32
	RegionID   *int32
	DistrictID *int32
	OrgID      *int32
}

type PointRepo interface {
	Create(ctx context.Context, p *models.Point) (int32, error)
	Update(ctx context.Context, p *models.Point) error
	Delete(ctx context.Context, id int32) error
	ListByPaligon(ctx context.Context, paligonID *int32) ([]*models.Point, error)
}

type DutyRepo interface {
	Create(ctx context.Context, d *models.Duty) (int32, error)
	Stop(ctx context.Context, sectionID int32, endedAt string) error
	List(ctx context.Context, filter DutyFilter) ([]*models.Duty, error)
	GetActive(ctx context.Context, sectionID int32) (*models.Duty, error)
	GetActiveDuties(ctx context.Context) ([]*models.Duty, error)
}

type DutyFilter struct {
	SectionID  *int32
	StartedAt  *string
	OrgID      *int32
	RegionID   *int32
	DistrictID *int32
}

type LocationRepo interface {
	Save(ctx context.Context, loc *models.Location) error
	GetLatestByPinfl(ctx context.Context, pinflHash string) (*models.Location, error)
	HasPointVisit(ctx context.Context, pinflHash string, pointID, dutyID int32) (bool, error)
	SavePointVisit(ctx context.Context, pinflHash string, pointID, dutyID int32) error
	SaveVehicleLocation(ctx context.Context, vl *models.VehicleLocation) error
	GetLatestVehicleLocation(ctx context.Context, plateNumber string) (*models.VehicleLocation, error)
}

type VehicleTracker interface {
	FetchAll(ctx context.Context) ([]*models.VehicleLocation, error)
}
