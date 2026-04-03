package models

import "time"

type Point struct {
	ID        int32     `json:"id"`
	PaligonID int32     `json:"paligon_id"`
	Order     int32     `json:"order"`
	Radius    int32     `json:"radius"`
	Latitude  float64   `json:"latitude"`
	Longitude float64   `json:"longitude"`
	StartTime string    `json:"start_time"`
	EndTime   string    `json:"end_time"`
	CreatedAt time.Time `json:"created_at"`
}
