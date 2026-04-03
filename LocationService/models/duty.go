package models

import "time"

type Assignment struct {
	ID        int32    `json:"id"`
	DutyID    int32    `json:"duty_id"`
	PaligonID int32    `json:"paligon_id"`
	Employees []string `json:"employees"`
	Vehicles  []string `json:"vehicles"`
}

type Duty struct {
	ID          int32        `json:"id"`
	SectionID   int32        `json:"section_id"`
	OrgID       int32        `json:"org_id"`
	RegionID    int32        `json:"region_id"`
	DistrictID  int32        `json:"district_id"`
	StartedAt   time.Time    `json:"started_at"`
	EndedAt     *time.Time   `json:"ended_at"`
	Status      string       `json:"status"`
	Assignments []Assignment `json:"assignments"`
}
