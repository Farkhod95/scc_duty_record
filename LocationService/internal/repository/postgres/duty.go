package postgres

import (
	"context"
	"fmt"
	"LocationService/internal/repository"
	"LocationService/models"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type dutyRepo struct {
	db *pgxpool.Pool
}

func NewDutyRepo(db *pgxpool.Pool) repository.DutyRepo {
	return &dutyRepo{db: db}
}

func (r *dutyRepo) Create(ctx context.Context, d *models.Duty) (int32, error) {
	tx, err := r.db.Begin(ctx)
	if err != nil {
		return 0, fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback(ctx)

	var dutyID int32
	err = tx.QueryRow(ctx,
		`INSERT INTO duties (section_id, org_id, region_id, district_id, started_at, status)
		 VALUES ($1, $2, $3, $4, $5, 'active') RETURNING id`,
		d.SectionID, d.OrgID, d.RegionID, d.DistrictID, d.StartedAt,
	).Scan(&dutyID)
	if err != nil {
		return 0, fmt.Errorf("insert duty: %w", err)
	}

	for _, a := range d.Assignments {
		var assignID int32
		err = tx.QueryRow(ctx,
			`INSERT INTO duty_assignments (duty_id, paligon_id) VALUES ($1, $2) RETURNING id`,
			dutyID, a.PaligonID,
		).Scan(&assignID)
		if err != nil {
			return 0, fmt.Errorf("insert assignment: %w", err)
		}

		for _, emp := range a.Employees {
			_, err = tx.Exec(ctx,
				`INSERT INTO duty_employees (assignment_id, pinfl_hash) VALUES ($1, $2)`,
				assignID, emp)
			if err != nil {
				return 0, fmt.Errorf("insert employee: %w", err)
			}
		}

		for _, plate := range a.Vehicles {
			_, err = tx.Exec(ctx,
				`INSERT INTO duty_transports (assignment_id, plate_number) VALUES ($1, $2)`,
				assignID, plate)
			if err != nil {
				return 0, fmt.Errorf("insert transport: %w", err)
			}
		}
	}

	if err := tx.Commit(ctx); err != nil {
		return 0, fmt.Errorf("commit: %w", err)
	}
	return dutyID, nil
}

func (r *dutyRepo) Stop(ctx context.Context, sectionID int32, endedAt string) error {
	_, err := r.db.Exec(ctx,
		`UPDATE duties SET ended_at=$1, status='stopped' WHERE section_id=$2 AND ended_at IS NULL`,
		endedAt, sectionID,
	)
	if err != nil {
		return fmt.Errorf("stop duty: %w", err)
	}
	return nil
}

func (r *dutyRepo) List(ctx context.Context, filter repository.DutyFilter) ([]*models.Duty, error) {
	query := `SELECT id, section_id, org_id, region_id, district_id, started_at
	          FROM duties WHERE 1=1`
	args := []any{}
	i := 1

	if filter.SectionID != nil {
		query += fmt.Sprintf(" AND section_id=$%d", i); args = append(args, *filter.SectionID); i++
	}
	if filter.OrgID != nil {
		query += fmt.Sprintf(" AND org_id=$%d", i); args = append(args, *filter.OrgID); i++
	}
	if filter.RegionID != nil {
		query += fmt.Sprintf(" AND region_id=$%d", i); args = append(args, *filter.RegionID); i++
	}
	if filter.DistrictID != nil {
		query += fmt.Sprintf(" AND district_id=$%d", i); args = append(args, *filter.DistrictID); i++
	}
	if filter.StartedAt != nil {
		query += fmt.Sprintf(" AND started_at::date=$%d", i); args = append(args, *filter.StartedAt); i++
	}
	_ = i
	query += " ORDER BY id DESC"

	rows, err := r.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("list duties: %w", err)
	}
	defer rows.Close()

	var duties []*models.Duty
	for rows.Next() {
		d := &models.Duty{}
		if err := rows.Scan(&d.ID, &d.SectionID, &d.OrgID, &d.RegionID, &d.DistrictID, &d.StartedAt); err != nil {
			return nil, fmt.Errorf("scan duty: %w", err)
		}
		duties = append(duties, d)
	}
	return duties, nil
}

func (r *dutyRepo) GetActive(ctx context.Context, sectionID int32) (*models.Duty, error) {
	d := &models.Duty{}
	err := r.db.QueryRow(ctx,
		`SELECT id, section_id, org_id, region_id, district_id, started_at
		 FROM duties WHERE section_id=$1 AND ended_at IS NULL LIMIT 1`,
		sectionID,
	).Scan(&d.ID, &d.SectionID, &d.OrgID, &d.RegionID, &d.DistrictID, &d.StartedAt)
	if err != nil {
		if err == pgx.ErrNoRows {
			return nil, nil
		}
		return nil, fmt.Errorf("get active duty: %w", err)
	}

	assignments, err := r.loadAssignments(ctx, d.ID)
	if err != nil {
		return nil, err
	}
	d.Assignments = assignments
	return d, nil
}

func (r *dutyRepo) GetActiveDuties(ctx context.Context) ([]*models.Duty, error) {
	rows, err := r.db.Query(ctx,
		`SELECT id, section_id, org_id, region_id, district_id, started_at
		 FROM duties WHERE ended_at IS NULL`)
	if err != nil {
		return nil, fmt.Errorf("get active duties: %w", err)
	}
	defer rows.Close()

	var duties []*models.Duty
	for rows.Next() {
		d := &models.Duty{}
		if err := rows.Scan(&d.ID, &d.SectionID, &d.OrgID, &d.RegionID, &d.DistrictID, &d.StartedAt); err != nil {
			return nil, fmt.Errorf("scan duty: %w", err)
		}
		duties = append(duties, d)
	}
	rows.Close()

	for _, d := range duties {
		a, err := r.loadAssignments(ctx, d.ID)
		if err != nil {
			return nil, err
		}
		d.Assignments = a
	}
	return duties, nil
}

func (r *dutyRepo) loadAssignments(ctx context.Context, dutyID int32) ([]models.Assignment, error) {
	rows, err := r.db.Query(ctx,
		`SELECT id, duty_id, paligon_id FROM duty_assignments WHERE duty_id=$1`, dutyID)
	if err != nil {
		return nil, fmt.Errorf("load assignments: %w", err)
	}
	defer rows.Close()

	var assignments []models.Assignment
	for rows.Next() {
		a := models.Assignment{}
		if err := rows.Scan(&a.ID, &a.DutyID, &a.PaligonID); err != nil {
			return nil, fmt.Errorf("scan assignment: %w", err)
		}
		assignments = append(assignments, a)
	}
	rows.Close()

	for i := range assignments {
		empRows, err := r.db.Query(ctx,
			`SELECT pinfl_hash FROM duty_employees WHERE assignment_id=$1`, assignments[i].ID)
		if err != nil {
			return nil, fmt.Errorf("load employees: %w", err)
		}
		for empRows.Next() {
			var ph string
			empRows.Scan(&ph)
			assignments[i].Employees = append(assignments[i].Employees, ph)
		}
		empRows.Close()

		vRows, err := r.db.Query(ctx,
			`SELECT plate_number FROM duty_transports WHERE assignment_id=$1`, assignments[i].ID)
		if err != nil {
			return nil, fmt.Errorf("load transports: %w", err)
		}
		for vRows.Next() {
			var pn string
			vRows.Scan(&pn)
			assignments[i].Vehicles = append(assignments[i].Vehicles, pn)
		}
		vRows.Close()
	}
	return assignments, nil
}
