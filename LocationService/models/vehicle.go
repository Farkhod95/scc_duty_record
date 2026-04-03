package models

import "time"

type VehicleLocation struct {
	ID          int64     `json:"id"`
	PlateNumber string    `json:"plate_number"`
	Latitude    float64   `json:"latitude"`
	Longitude   float64   `json:"longitude"`
	Speed       float64   `json:"speed"`
	EngineOn    int32     `json:"engine_on"`
	TpTimestamp int64     `json:"tp_timestamp"`
	RecordedAt  time.Time `json:"recorded_at"`
}
