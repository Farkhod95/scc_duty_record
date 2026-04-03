package postgres

import (
	"context"
	"encoding/json"
	"fmt"
	"LocationService/internal/repository"
	"LocationService/models"

	"github.com/jackc/pgx/v5/pgxpool"
)

type paligonRepo struct {
	db *pgxpool.Pool
}

func NewPaligonRepo(db *pgxpool.Pool) repository.PaligonRepo {
	return &paligonRepo{db: db}
}

func (r *paligonRepo) Create(ctx context.Context, p *models.Paligon) (int32, error) {
	boundary, err := json.Marshal(p.BoundaryData)
	if err != nil {
		return 0, fmt.Errorf("marshal boundary: %w", err)
	}
	var id int32
	err = r.db.QueryRow(ctx,
		`INSERT INTO paligons (region_id, district_id, org_id, boundary_data)
		 VALUES ($1, $2, $3, $4) RETURNING id`,
		p.RegionID, p.DistrictID, p.OrgID, boundary,
	).Scan(&id)
	if err != nil {
		return 0, fmt.Errorf("create paligon: %w", err)
	}
	return id, nil
}

func (r *paligonRepo) Update(ctx context.Context, p *models.Paligon) error {
	boundary, err := json.Marshal(p.BoundaryData)
	if err != nil {
		return fmt.Errorf("marshal boundary: %w", err)
	}
	_, err = r.db.Exec(ctx,
		`UPDATE paligons SET region_id=$1, district_id=$2, org_id=$3, boundary_data=$4
		 WHERE id=$5`,
		p.RegionID, p.DistrictID, p.OrgID, boundary, p.ID,
	)
	if err != nil {
		return fmt.Errorf("update paligon: %w", err)
	}
	return nil
}

func (r *paligonRepo) Delete(ctx context.Context, id int32) error {
	_, err := r.db.Exec(ctx, `DELETE FROM paligons WHERE id=$1`, id)
	if err != nil {
		return fmt.Errorf("delete paligon: %w", err)
	}
	return nil
}

func (r *paligonRepo) List(ctx context.Context, filter repository.PaligonFilter) ([]*models.Paligon, error) {
	query := `SELECT id, region_id, district_id, org_id, boundary_data FROM paligons WHERE 1=1`
	args := []any{}
	i := 1
	if filter.ID != nil {
		query += fmt.Sprintf(" AND id=$%d", i); args = append(args, *filter.ID); i++
	}
	if filter.RegionID != nil {
		query += fmt.Sprintf(" AND region_id=$%d", i); args = append(args, *filter.RegionID); i++
	}
	if filter.DistrictID != nil {
		query += fmt.Sprintf(" AND district_id=$%d", i); args = append(args, *filter.DistrictID); i++
	}
	if filter.OrgID != nil {
		query += fmt.Sprintf(" AND org_id=$%d", i); args = append(args, *filter.OrgID); i++
	}
	_ = i

	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("list paligons: %w", err)
	}
	defer rows.Close()

	var result []*models.Paligon
	for rows.Next() {
		p := &models.Paligon{}
		var boundaryRaw []byte
		if err := rows.Scan(&p.ID, &p.RegionID, &p.DistrictID, &p.OrgID, &boundaryRaw); err != nil {
			return nil, fmt.Errorf("scan paligon: %w", err)
		}
		if err := json.Unmarshal(boundaryRaw, &p.BoundaryData); err != nil {
			return nil, fmt.Errorf("unmarshal boundary: %w", err)
		}
		result = append(result, p)
	}
	return result, nil
}

func (r *paligonRepo) GetByID(ctx context.Context, id int32) (*models.Paligon, error) {
	p := &models.Paligon{}
	var boundaryRaw []byte
	err := r.db.QueryRow(ctx,
		`SELECT id, region_id, district_id, org_id, boundary_data FROM paligons WHERE id=$1`, id,
	).Scan(&p.ID, &p.RegionID, &p.DistrictID, &p.OrgID, &boundaryRaw)
	if err != nil {
		return nil, fmt.Errorf("get paligon: %w", err)
	}
	if err := json.Unmarshal(boundaryRaw, &p.BoundaryData); err != nil {
		return nil, fmt.Errorf("unmarshal boundary: %w", err)
	}
	return p, nil
}
