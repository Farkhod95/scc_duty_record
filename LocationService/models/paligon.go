package models

import "time"

type Coordinate struct {
	Latitude  float64 `json:"latitude"`
	Longitude float64 `json:"longitude"`
}

type Paligon struct {
	ID           int32        `json:"id"`
	RegionID     int32        `json:"region_id"`
	DistrictID   int32        `json:"district_id"`
	OrgID        int32        `json:"org_id"`
	BoundaryData []Coordinate `json:"boundary_data"`
	CreatedAt    time.Time    `json:"created_at"`
}
