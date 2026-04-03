package service

import (
	"context"
	"LocationService/models"
	"LocationService/proto"
)

type LocationService interface {
	PaligonCreate(ctx context.Context, req *proto.PaligonRequest) (int32, error)
	PaligonDelete(ctx context.Context, id int32) error
	PaligonList(ctx context.Context, req *proto.PaligonFilterRequest) ([]*models.Paligon, error)

	PointCreate(ctx context.Context, req *proto.PointRequest) (int32, error)
	PointDelete(ctx context.Context, id int32) error
	PointList(ctx context.Context, paligonID *int32) ([]*models.Point, error)

	DutyCreate(ctx context.Context, req *proto.DutyRequest) (int32, error)
	DutyStop(ctx context.Context, sectionID int32, endedAt string) error
	DutyList(ctx context.Context, req *proto.DutyListRequest) ([]*models.Duty, error)
	DutyInfo(ctx context.Context, sectionID int32) (*proto.DutyInfoResponse, error)

	SaveLocation(ctx context.Context, req *proto.LocationRequest) error

	RegisterAlarmClient(sectionID int32, ch chan *proto.AlarmEvent)
	UnregisterAlarmClient(sectionID int32, ch chan *proto.AlarmEvent)

	RunVehiclePoller(ctx context.Context)
}
