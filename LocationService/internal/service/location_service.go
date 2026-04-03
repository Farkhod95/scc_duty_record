package service

import (
	"context"
	"fmt"
	"log"
	"math"
	"strings"
	"sync"
	"time"

	"LocationService/internal/repository"
	"LocationService/models"
	"LocationService/proto"
)

type locationService struct {
	paligonRepo    repository.PaligonRepo
	pointRepo      repository.PointRepo
	dutyRepo       repository.DutyRepo
	locationRepo   repository.LocationRepo
	vehicleTracker repository.VehicleTracker
	pollInterval   time.Duration

	mu      sync.RWMutex
	streams map[int32][]chan *proto.AlarmEvent
}

func NewLocationService(
	pr repository.PaligonRepo,
	ptr repository.PointRepo,
	dr repository.DutyRepo,
	lr repository.LocationRepo,
	vt repository.VehicleTracker,
	pollInterval time.Duration,
) LocationService {
	return &locationService{
		paligonRepo:    pr,
		pointRepo:      ptr,
		dutyRepo:       dr,
		locationRepo:   lr,
		vehicleTracker: vt,
		pollInterval:   pollInterval,
		streams:        make(map[int32][]chan *proto.AlarmEvent),
	}
}

// ─── Paligon ───────────────────────────────────────────────────────────────

func (s *locationService) PaligonCreate(ctx context.Context, req *proto.PaligonRequest) (int32, error) {
	p := &models.Paligon{
		ID:         req.Id,
		RegionID:   req.RegionId,
		DistrictID: req.DistrictId,
		OrgID:      req.OrgId,
	}
	for _, c := range req.BoundaryData {
		p.BoundaryData = append(p.BoundaryData, models.Coordinate{
			Latitude: c.Latitude, Longitude: c.Longitude,
		})
	}
	if req.Id > 0 {
		if err := s.paligonRepo.Update(ctx, p); err != nil {
			return 0, fmt.Errorf("paligon update: %w", err)
		}
		return req.Id, nil
	}
	id, err := s.paligonRepo.Create(ctx, p)
	if err != nil {
		return 0, fmt.Errorf("paligon create: %w", err)
	}
	return id, nil
}

func (s *locationService) PaligonDelete(ctx context.Context, id int32) error {
	if err := s.paligonRepo.Delete(ctx, id); err != nil {
		return fmt.Errorf("paligon delete: %w", err)
	}
	return nil
}

func (s *locationService) PaligonList(ctx context.Context, req *proto.PaligonFilterRequest) ([]*models.Paligon, error) {
	filter := repository.PaligonFilter{
		ID:         req.Id,
		RegionID:   req.RegionId,
		DistrictID: req.DistrictId,
		OrgID:      req.OrgId,
	}
	list, err := s.paligonRepo.List(ctx, filter)
	if err != nil {
		return nil, fmt.Errorf("paligon list: %w", err)
	}
	return list, nil
}

// ─── Point ─────────────────────────────────────────────────────────────────

func (s *locationService) PointCreate(ctx context.Context, req *proto.PointRequest) (int32, error) {
	p := &models.Point{
		ID:        req.Id,
		PaligonID: req.PaligonId,
		Order:     req.Order,
		Radius:    req.Radius,
		Latitude:  req.Latitude,
		Longitude: req.Longitude,
		StartTime: req.StartTime,
		EndTime:   req.EndTime,
	}
	if req.Id > 0 {
		if err := s.pointRepo.Update(ctx, p); err != nil {
			return 0, fmt.Errorf("point update: %w", err)
		}
		return req.Id, nil
	}
	id, err := s.pointRepo.Create(ctx, p)
	if err != nil {
		return 0, fmt.Errorf("point create: %w", err)
	}
	return id, nil
}

func (s *locationService) PointDelete(ctx context.Context, id int32) error {
	return s.pointRepo.Delete(ctx, id)
}

func (s *locationService) PointList(ctx context.Context, paligonID *int32) ([]*models.Point, error) {
	return s.pointRepo.ListByPaligon(ctx, paligonID)
}

// ─── Duty ──────────────────────────────────────────────────────────────────

func (s *locationService) DutyCreate(ctx context.Context, req *proto.DutyRequest) (int32, error) {
	existing, err := s.dutyRepo.GetActive(ctx, req.SectionId)
	if err != nil {
		return 0, fmt.Errorf("check active duty: %w", err)
	}
	if existing != nil {
		return 0, fmt.Errorf("already exists: active duty for section %d", req.SectionId)
	}

	startedAt, err := time.Parse(time.RFC3339, req.StartedAt)
	if err != nil {
		startedAt = time.Now()
	}

	d := &models.Duty{
		SectionID:  req.SectionId,
		OrgID:      req.OrgId,
		RegionID:   req.RegionId,
		DistrictID: req.DistrictId,
		StartedAt:  startedAt,
	}
	for _, a := range req.Assignments {
		assign := models.Assignment{
			PaligonID: a.PaligonId,
			Employees: a.Employees,
			Vehicles:  a.Vehicles,
		}
		d.Assignments = append(d.Assignments, assign)
	}

	id, err := s.dutyRepo.Create(ctx, d)
	if err != nil {
		return 0, fmt.Errorf("duty create: %w", err)
	}
	return id, nil
}

func (s *locationService) DutyStop(ctx context.Context, sectionID int32, endedAt string) error {
	if err := s.dutyRepo.Stop(ctx, sectionID, endedAt); err != nil {
		return fmt.Errorf("duty stop: %w", err)
	}
	return nil
}

func (s *locationService) DutyList(ctx context.Context, req *proto.DutyListRequest) ([]*models.Duty, error) {
	filter := repository.DutyFilter{
		SectionID:  req.SectionId,
		StartedAt:  req.StartedAt,
		OrgID:      req.OrgId,
		RegionID:   req.RegionId,
		DistrictID: req.DistrictId,
	}
	return s.dutyRepo.List(ctx, filter)
}

func (s *locationService) DutyInfo(ctx context.Context, sectionID int32) (*proto.DutyInfoResponse, error) {
	duty, err := s.dutyRepo.GetActive(ctx, sectionID)
	if err != nil {
		return nil, fmt.Errorf("get active duty: %w", err)
	}
	if duty == nil {
		return nil, fmt.Errorf("not found: no active duty for section %d", sectionID)
	}

	resp := &proto.DutyInfoResponse{SectionId: sectionID}

	for _, a := range duty.Assignments {
		paligon, err := s.paligonRepo.GetByID(ctx, a.PaligonID)
		if err != nil {
			return nil, fmt.Errorf("get paligon: %w", err)
		}

		info := &proto.AssignmentInfo{PaligonId: a.PaligonID}

		for _, ph := range a.Employees {
			loc, err := s.locationRepo.GetLatestByPinfl(ctx, ph)
			ei := &proto.EmployeeInfo{PinflHash: ph, PointId: -1}
			if loc != nil && err == nil {
				ei.Latitude = loc.Latitude
				ei.Longitude = loc.Longitude
				ei.UpdatedAt = loc.RecordedAt.UnixMilli()
				ei.InPolygon = pointInPolygon(loc.Latitude, loc.Longitude, paligon.BoundaryData)

				points, _ := s.pointRepo.ListByPaligon(ctx, &a.PaligonID)
				for _, pt := range points {
					dist := haversineMeters(loc.Latitude, loc.Longitude, pt.Latitude, pt.Longitude)
					if dist <= float64(pt.Radius) {
						ei.AtPoint = true
						ei.PointId = pt.ID
						break
					}
				}
			}
			info.Employees = append(info.Employees, ei)
		}

		for _, plate := range a.Vehicles {
			vl, err := s.locationRepo.GetLatestVehicleLocation(ctx, plate)
			vi := &proto.VehicleInfo{PlateNumber: plate}
			if vl != nil && err == nil {
				vi.Latitude = vl.Latitude
				vi.Longitude = vl.Longitude
				vi.UpdatedAt = vl.RecordedAt.UnixMilli()
				vi.InPolygon = pointInPolygon(vl.Latitude, vl.Longitude, paligon.BoundaryData)
			}
			info.Vehicles = append(info.Vehicles, vi)
		}

		resp.Assignments = append(resp.Assignments, info)
	}
	return resp, nil
}

// ─── Location ──────────────────────────────────────────────────────────────

func (s *locationService) SaveLocation(ctx context.Context, req *proto.LocationRequest) error {
	if req.PinflHash == "" {
		return fmt.Errorf("invalid argument: pinfl_hash is required")
	}

	ts := time.UnixMilli(req.Timestamp)
	if req.Timestamp == 0 {
		ts = time.Now()
	}

	loc := &models.Location{
		PinflHash: req.PinflHash,
		Latitude:  req.Latitude,
		Longitude: req.Longitude,
		Accuracy:  req.Accuracy,
		RecordedAt: ts,
	}
	if err := s.locationRepo.Save(ctx, loc); err != nil {
		return fmt.Errorf("save location: %w", err)
	}

	duties, err := s.dutyRepo.GetActiveDuties(ctx)
	if err != nil {
		return fmt.Errorf("get active duties: %w", err)
	}

	now := time.Now()

	for _, duty := range duties {
		for _, a := range duty.Assignments {
			if !containsEmployee(a.Employees, req.PinflHash) {
				continue
			}

			paligon, err := s.paligonRepo.GetByID(ctx, a.PaligonID)
			if err != nil {
				continue
			}

			inPoly := pointInPolygon(req.Latitude, req.Longitude, paligon.BoundaryData)
			if !inPoly {
				s.fanOut(duty.SectionID, &proto.AlarmEvent{
					SectionId: duty.SectionID,
					Type:      "OUT_OF_POLYGON",
					PaligonId: a.PaligonID,
					Latitude:  req.Latitude,
					Longitude: req.Longitude,
					Message:   fmt.Sprintf("Xodim %s polygondan chiqdi", req.PinflHash),
					Timestamp: time.Now().UnixMilli(),
					Subject:   &proto.AlarmEvent_PinflHash{PinflHash: req.PinflHash},
				})
			}

			points, _ := s.pointRepo.ListByPaligon(ctx, &a.PaligonID)
			for _, pt := range points {
				dist := haversineMeters(req.Latitude, req.Longitude, pt.Latitude, pt.Longitude)
				inTime := isInTimeWindow(now, pt.StartTime, pt.EndTime)
				pastEnd := isPastEndTime(now, pt.EndTime)

				if dist <= float64(pt.Radius) && inTime {
					has, _ := s.locationRepo.HasPointVisit(ctx, req.PinflHash, pt.ID, duty.ID)
					if !has {
						s.locationRepo.SavePointVisit(ctx, req.PinflHash, pt.ID, duty.ID)
					}
				}

				if pastEnd {
					has, _ := s.locationRepo.HasPointVisit(ctx, req.PinflHash, pt.ID, duty.ID)
					if !has {
						s.fanOut(duty.SectionID, &proto.AlarmEvent{
							SectionId: duty.SectionID,
							Type:      "POINT_MISSED",
							PaligonId: a.PaligonID,
							PointId:   pt.ID,
							Latitude:  req.Latitude,
							Longitude: req.Longitude,
							Message:   fmt.Sprintf("Xodim %s nuqtaga bormadi (point_id=%d)", req.PinflHash, pt.ID),
							Timestamp: time.Now().UnixMilli(),
							Subject:   &proto.AlarmEvent_PinflHash{PinflHash: req.PinflHash},
						})
					}
				}
			}
		}
	}
	return nil
}

// ─── AlarmStream ───────────────────────────────────────────────────────────

func (s *locationService) RegisterAlarmClient(sectionID int32, ch chan *proto.AlarmEvent) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.streams[sectionID] = append(s.streams[sectionID], ch)
}

func (s *locationService) UnregisterAlarmClient(sectionID int32, ch chan *proto.AlarmEvent) {
	s.mu.Lock()
	defer s.mu.Unlock()
	list := s.streams[sectionID]
	for i, c := range list {
		if c == ch {
			s.streams[sectionID] = append(list[:i], list[i+1:]...)
			break
		}
	}
}

func (s *locationService) fanOut(sectionID int32, event *proto.AlarmEvent) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	for _, ch := range s.streams[sectionID] {
		select {
		case ch <- event:
		default:
		}
	}
}

// ─── Vehicle Poller ────────────────────────────────────────────────────────

func (s *locationService) RunVehiclePoller(ctx context.Context) {
	ticker := time.NewTicker(s.pollInterval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if err := s.pollVehicles(ctx); err != nil {
				log.Printf("vehicle poll error: %v", err)
			}
		}
	}
}

func (s *locationService) pollVehicles(ctx context.Context) error {
	duties, err := s.dutyRepo.GetActiveDuties(ctx)
	if err != nil {
		return fmt.Errorf("get active duties: %w", err)
	}
	if len(duties) == 0 {
		return nil
	}

	vehicles, err := s.vehicleTracker.FetchAll(ctx)
	if err != nil {
		return fmt.Errorf("fetch vehicles: %w", err)
	}

	vehicleMap := make(map[string]*models.VehicleLocation, len(vehicles))
	for _, v := range vehicles {
		vehicleMap[strings.ToUpper(v.PlateNumber)] = v
	}

	for _, duty := range duties {
		for _, a := range duty.Assignments {
			paligon, err := s.paligonRepo.GetByID(ctx, a.PaligonID)
			if err != nil {
				continue
			}

			for _, plate := range a.Vehicles {
				vl, ok := vehicleMap[strings.ToUpper(plate)]
				if !ok {
					continue
				}
				vl.PlateNumber = plate
				s.locationRepo.SaveVehicleLocation(ctx, vl)

				if !pointInPolygon(vl.Latitude, vl.Longitude, paligon.BoundaryData) {
					s.fanOut(duty.SectionID, &proto.AlarmEvent{
						SectionId: duty.SectionID,
						Type:      "OUT_OF_POLYGON",
						PaligonId: a.PaligonID,
						Latitude:  vl.Latitude,
						Longitude: vl.Longitude,
						Message:   fmt.Sprintf("Mashina %s polygondan chiqdi", plate),
						Timestamp: time.Now().UnixMilli(),
						Subject:   &proto.AlarmEvent_PlateNumber{PlateNumber: plate},
					})
				}
			}
		}
	}
	return nil
}

// ─── Algoritmlar ───────────────────────────────────────────────────────────

func haversineMeters(lat1, lon1, lat2, lon2 float64) float64 {
	const R = 6371000
	φ1 := lat1 * math.Pi / 180
	φ2 := lat2 * math.Pi / 180
	Δφ := (lat2 - lat1) * math.Pi / 180
	Δλ := (lon2 - lon1) * math.Pi / 180
	a := math.Sin(Δφ/2)*math.Sin(Δφ/2) +
		math.Cos(φ1)*math.Cos(φ2)*math.Sin(Δλ/2)*math.Sin(Δλ/2)
	return R * 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))
}

func pointInPolygon(lat, lon float64, boundary []models.Coordinate) bool {
	inside := false
	j := len(boundary) - 1
	for i := 0; i < len(boundary); i++ {
		xi, yi := boundary[i].Longitude, boundary[i].Latitude
		xj, yj := boundary[j].Longitude, boundary[j].Latitude
		if ((yi > lat) != (yj > lat)) &&
			(lon < (xj-xi)*(lat-yi)/(yj-yi)+xi) {
			inside = !inside
		}
		j = i
	}
	return inside
}

func containsEmployee(employees []string, pinflHash string) bool {
	for _, e := range employees {
		if e == pinflHash {
			return true
		}
	}
	return false
}

func isInTimeWindow(now time.Time, startTime, endTime string) bool {
	if startTime == "" || endTime == "" {
		return true
	}
	nowStr := now.Format("15:04:05")
	return nowStr >= startTime && nowStr <= endTime
}

func isPastEndTime(now time.Time, endTime string) bool {
	if endTime == "" {
		return false
	}
	return now.Format("15:04:05") > endTime
}
