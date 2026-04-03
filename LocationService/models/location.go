package models

import "time"

type Location struct {
	ID         int64     `json:"id"`
	PinflHash  string    `json:"pinfl_hash"`
	Latitude   float64   `json:"latitude"`
	Longitude  float64   `json:"longitude"`
	Accuracy   float64   `json:"accuracy"`
	RecordedAt time.Time `json:"recorded_at"`
}
