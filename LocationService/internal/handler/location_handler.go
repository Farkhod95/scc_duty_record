package handler

import (
	"context"
	"strings"

	"LocationService/internal/service"
	"LocationService/proto"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type LocationHandler struct {
	proto.UnimplementedLocationServiceServer
	svc service.LocationService
}

func NewLocationHandler(svc service.LocationService) *LocationHandler {
	return &LocationHandler{svc: svc}
}

// ─── Paligon ───────────────────────────────────────────────────────────────

func (h *LocationHandler) PaligonCreate(ctx context.Context, req *proto.PaligonRequest) (*proto.PaligonResponse, error) {
	if req.OrgId == 0 {
		return nil, status.Error(codes.InvalidArgument, "org_id is required")
	}
	id, err := h.svc.PaligonCreate(ctx, req)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "paligon create: %v", err)
	}
	return &proto.PaligonResponse{Id: id}, nil
}

func (h *LocationHandler) PaligonDelete(ctx context.Context, req *proto.PaligonDeleteRequest) (*proto.Empty, error) {
	if req.Id == 0 {
		return nil, status.Error(codes.InvalidArgument, "id is required")
	}
	if err := h.svc.PaligonDelete(ctx, req.Id); err != nil {
		return nil, status.Errorf(codes.Internal, "paligon delete: %v", err)
	}
	return &proto.Empty{}, nil
}

func (h *LocationHandler) PaligonList(ctx context.Context, req *proto.PaligonFilterRequest) (*proto.PaligonListResponse, error) {
	list, err := h.svc.PaligonList(ctx, req)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "paligon list: %v", err)
	}
	resp := &proto.PaligonListResponse{}
	for _, p := range list {
		pr := &proto.PaligonRequest{
			Id:         p.ID,
			RegionId:   p.RegionID,
			DistrictId: p.DistrictID,
			OrgId:      p.OrgID,
		}
		for _, c := range p.BoundaryData {
			pr.BoundaryData = append(pr.BoundaryData, &proto.Coordinate{
				Latitude: c.Latitude, Longitude: c.Longitude,
			})
		}
		resp.Paligons = append(resp.Paligons, pr)
	}
	return resp, nil
}

// ─── Point ─────────────────────────────────────────────────────────────────

func (h *LocationHandler) PointCreate(ctx context.Context, req *proto.PointRequest) (*proto.PointResponse, error) {
	if req.PaligonId == 0 {
		return nil, status.Error(codes.InvalidArgument, "paligon_id is required")
	}
	id, err := h.svc.PointCreate(ctx, req)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "point create: %v", err)
	}
	return &proto.PointResponse{Id: id}, nil
}

func (h *LocationHandler) PointDelete(ctx context.Context, req *proto.PointDeleteRequest) (*proto.Empty, error) {
	if req.Id == 0 {
		return nil, status.Error(codes.InvalidArgument, "id is required")
	}
	if err := h.svc.PointDelete(ctx, req.Id); err != nil {
		return nil, status.Errorf(codes.Internal, "point delete: %v", err)
	}
	return &proto.Empty{}, nil
}

func (h *LocationHandler) PointList(ctx context.Context, req *proto.PointListRequest) (*proto.PointListResponse, error) {
	list, err := h.svc.PointList(ctx, req.PaligonId)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "point list: %v", err)
	}
	resp := &proto.PointListResponse{}
	for _, p := range list {
		resp.Points = append(resp.Points, &proto.PointRequest{
			Id:        p.ID,
			PaligonId: p.PaligonID,
			Order:     p.Order,
			Radius:    p.Radius,
			Latitude:  p.Latitude,
			Longitude: p.Longitude,
			StartTime: p.StartTime,
			EndTime:   p.EndTime,
		})
	}
	return resp, nil
}

// ─── Duty ──────────────────────────────────────────────────────────────────

func (h *LocationHandler) DutyCreate(ctx context.Context, req *proto.DutyRequest) (*proto.DutyResponse, error) {
	if req.SectionId == 0 {
		return nil, status.Error(codes.InvalidArgument, "section_id is required")
	}
	id, err := h.svc.DutyCreate(ctx, req)
	if err != nil {
		if strings.Contains(err.Error(), "already exists") {
			return nil, status.Errorf(codes.AlreadyExists, "%v", err)
		}
		return nil, status.Errorf(codes.Internal, "duty create: %v", err)
	}
	return &proto.DutyResponse{Id: id}, nil
}

func (h *LocationHandler) DutyStop(ctx context.Context, req *proto.StopDutyRequest) (*proto.Empty, error) {
	if req.SectionId == 0 {
		return nil, status.Error(codes.InvalidArgument, "section_id is required")
	}
	if err := h.svc.DutyStop(ctx, req.SectionId, req.EndedAt); err != nil {
		return nil, status.Errorf(codes.Internal, "duty stop: %v", err)
	}
	return &proto.Empty{}, nil
}

func (h *LocationHandler) DutyList(ctx context.Context, req *proto.DutyListRequest) (*proto.DutyListResponse, error) {
	duties, err := h.svc.DutyList(ctx, req)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "duty list: %v", err)
	}
	resp := &proto.DutyListResponse{}
	for _, d := range duties {
		dr := &proto.DutyRequest{
			SectionId: d.SectionID,
			OrgId:     d.OrgID,
			RegionId:  d.RegionID,
			StartedAt: d.StartedAt.Format("2006-01-02T15:04:05Z07:00"),
		}
		resp.Duties = append(resp.Duties, dr)
	}
	return resp, nil
}

func (h *LocationHandler) DutyInfo(ctx context.Context, req *proto.DutyInfoRequest) (*proto.DutyInfoResponse, error) {
	if req.SectionId == 0 {
		return nil, status.Error(codes.InvalidArgument, "section_id is required")
	}
	resp, err := h.svc.DutyInfo(ctx, req.SectionId)
	if err != nil {
		if strings.Contains(err.Error(), "not found") {
			return nil, status.Errorf(codes.NotFound, "%v", err)
		}
		return nil, status.Errorf(codes.Internal, "duty info: %v", err)
	}
	return resp, nil
}

// ─── Location ──────────────────────────────────────────────────────────────

func (h *LocationHandler) Location(ctx context.Context, req *proto.LocationRequest) (*proto.Empty, error) {
	if req.PinflHash == "" {
		return nil, status.Error(codes.InvalidArgument, "pinfl_hash is required")
	}
	if err := h.svc.SaveLocation(ctx, req); err != nil {
		if strings.Contains(err.Error(), "invalid argument") {
			return nil, status.Errorf(codes.InvalidArgument, "%v", err)
		}
		return nil, status.Errorf(codes.Internal, "save location: %v", err)
	}
	return &proto.Empty{}, nil
}

// ─── AlarmStream ───────────────────────────────────────────────────────────

func (h *LocationHandler) AlarmStream(req *proto.AlarmRequest, stream proto.LocationService_AlarmStreamServer) error {
	ch := make(chan *proto.AlarmEvent, 32)
	h.svc.RegisterAlarmClient(req.SectionId, ch)
	defer h.svc.UnregisterAlarmClient(req.SectionId, ch)

	for {
		select {
		case <-stream.Context().Done():
			return nil
		case event, ok := <-ch:
			if !ok {
				return nil
			}
			if err := stream.Send(event); err != nil {
				return status.Errorf(codes.Internal, "send alarm: %v", err)
			}
		}
	}
}
