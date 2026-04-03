package external

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
	"LocationService/internal/repository"
	"LocationService/models"
)

type vehicleTracker struct {
	apiURL string
	token  string
	client *http.Client
}

func NewVehicleTracker(apiURL, token string) repository.VehicleTracker {
	return &vehicleTracker{
		apiURL: apiURL,
		token:  token,
		client: &http.Client{Timeout: 5 * time.Second},
	}
}

type apiResponse struct {
	Result []apiVehicle `json:"result"`
	Error  interface{}  `json:"error"`
}

type apiVehicle struct {
	PlateNumber string   `json:"plateNumber"`
	Lat         *float64 `json:"lat"`      // null bo'lishi mumkin — koordinata yo'q
	Lon         *float64 `json:"lon"`      // null bo'lishi mumkin — koordinata yo'q
	TpTimestamp *int64   `json:"tpTimestamp"`
	Speed       *float64 `json:"speed"`
	EngineOn    *int32   `json:"engineOn"`
}

func (t *vehicleTracker) FetchAll(ctx context.Context) ([]*models.VehicleLocation, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, t.apiURL, nil)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Authorization", "Bearer "+t.token)

	resp, err := t.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch vehicles: %w", err)
	}
	defer resp.Body.Close()

	var apiResp apiResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	result := make([]*models.VehicleLocation, 0, len(apiResp.Result))
	for _, v := range apiResp.Result {
		// Koordinatasi yo'q mashinalarni o'tkazib yuboramiz
		if v.Lat == nil || v.Lon == nil || v.PlateNumber == "" {
			continue
		}
		vl := &models.VehicleLocation{
			PlateNumber: v.PlateNumber,
			Latitude:    *v.Lat,
			Longitude:   *v.Lon,
		}
		if v.Speed != nil {
			vl.Speed = *v.Speed
		}
		if v.EngineOn != nil {
			vl.EngineOn = *v.EngineOn
		}
		if v.TpTimestamp != nil {
			vl.TpTimestamp = *v.TpTimestamp
		}
		result = append(result, vl)
	}
	return result, nil
}
