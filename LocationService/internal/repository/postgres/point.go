package postgres

import (
	"context"
	"fmt"
	"LocationService/internal/repository"
	"LocationService/models"

	"github.com/jackc/pgx/v5/pgxpool"
)

type pointRepo struct {
	db *pgxpool.Pool
}

func NewPointRepo(db *pgxpool.Pool) repository.PointRepo {
	return &pointRepo{db: db}
}

func (r *pointRepo) Create(ctx context.Context, p *models.Point) (int32, error) {
	var id int32
	err := r.db.QueryRow(ctx,
		`INSERT INTO points (paligon_id, "order", radius, latitude, longitude, start_time, end_time)
		 VALUES ($1, $2, $3, $4, $5, NULLIF($6,'')::time, NULLIF($7,'')::time) RETURNING id`,
		p.PaligonID, p.Order, p.Radius, p.Latitude, p.Longitude, p.StartTime, p.EndTime,
	).Scan(&id)
	if err != nil {
		return 0, fmt.Errorf("create point: %w", err)
	}
	return id, nil
}

func (r *pointRepo) Update(ctx context.Context, p *models.Point) error {
	_, err := r.db.Exec(ctx,
		`UPDATE points SET paligon_id=$1, "order"=$2, radius=$3, latitude=$4, longitude=$5,
		 start_time=NULLIF($6,'')::time, end_time=NULLIF($7,'')::time WHERE id=$8`,
		p.PaligonID, p.Order, p.Radius, p.Latitude, p.Longitude, p.StartTime, p.EndTime, p.ID,
	)
	if err != nil {
		return fmt.Errorf("update point: %w", err)
	}
	return nil
}

func (r *pointRepo) Delete(ctx context.Context, id int32) error {
	_, err := r.db.Exec(ctx, `DELETE FROM points WHERE id=$1`, id)
	if err != nil {
		return fmt.Errorf("delete point: %w", err)
	}
	return nil
}

func (r *pointRepo) ListByPaligon(ctx context.Context, paligonID *int32) ([]*models.Point, error) {
	query := `SELECT id, paligon_id, "order", radius, latitude, longitude,
	           COALESCE(start_time::text,''), COALESCE(end_time::text,'')
	           FROM points WHERE 1=1`
	args := []any{}
	if paligonID != nil {
		query += " AND paligon_id=$1"
		args = append(args, *paligonID)
	}
	query += ` ORDER BY "order"`

	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("list points: %w", err)
	}
	defer rows.Close()

	var result []*models.Point
	for rows.Next() {
		p := &models.Point{}
		if err := rows.Scan(&p.ID, &p.PaligonID, &p.Order, &p.Radius,
			&p.Latitude, &p.Longitude, &p.StartTime, &p.EndTime); err != nil {
			return nil, fmt.Errorf("scan point: %w", err)
		}
		result = append(result, p)
	}
	return result, nil
}
