# LocationService — Claude Code Guide

## Loyiha haqida

Go tilida yozilgan gRPC-based servis. Maqsad: xodimlar va mashinalarning GPS lokatsiyasini real-vaqtda kuzatib, ular biriktirilgan polygon hududda va nuqtalarda borligini aniqlash.

## Texnologiyalar

- **Go 1.22+**
- **gRPC** — `proto/location.proto` asosida
- **PostgreSQL** — pgx/v5 driver
- **External HTTP** — mashina GPS: `http://25.1.1.217:80/api/mobject/lastData`
- **Module nomi:** `LocationService`

## Papka strukturasi

```
LocationService/
├── CLAUDE.md
├── cmd/
│   └── main.go                        # DI wiring + gRPC server start
├── proto/
│   ├── location.proto                 # gRPC kontrakt (o'zgartirma)
│   ├── location.pb.go                 # generated (o'zgartirma)
│   └── location_grpc.pb.go            # generated (o'zgartirma)
├── config/
│   └── config.go                      # env dan o'qish
├── models/
│   ├── paligon.go
│   ├── point.go
│   ├── duty.go
│   ├── location.go
│   └── vehicle.go
├── internal/
│   ├── handler/
│   │   └── location_handler.go        # gRPC → Service interface
│   ├── service/
│   │   ├── interfaces.go              # LocationService interface
│   │   └── location_service.go        # biznes logika
│   └── repository/
│       ├── interfaces.go              # repo interface lar
│       ├── postgres/
│       │   ├── paligon.go
│       │   ├── point.go
│       │   ├── duty.go
│       │   └── location.go
│       └── external/
│           └── vehicle_tracker.go    # HTTP GET mashina GPS
└── migrations/
    └── 001_init.sql
```

## Asosiy qoidalar

### Arxitektura (buzilmasin)
```
gRPC Request
     ↓
  Handler          ← faqat proto type va service interface ni biladi
     ↓ (interface)
  Service          ← barcha biznes logika shu yerda
     ↓ (interface)
 Repository        ← faqat DB/HTTP operatsiyalar
     ↓
 PostgreSQL / External HTTP
```

- Handler hech qachon `*pgxpool.Pool` yoki repo struct ni import qilmaydi
- Service hech qachon `pgx`, `sql` paketlarini import qilmaydi
- Repository hech qachon proto paketini import qilmaydi

### Error handling
```go
// Handler da grpc status ishlatiladi:
import "google.golang.org/grpc/status"
import "google.golang.org/grpc/codes"

return nil, status.Errorf(codes.Internal, "save location: %v", err)
return nil, status.Errorf(codes.NotFound, "duty not found for section %d", req.SectionId)
return nil, status.Errorf(codes.InvalidArgument, "pinfl_hash is required")
```

- Repo dan kelgan error lar service da wrap qilinadi (`fmt.Errorf("...: %w", err)`)
- Handler da service error grpc status ga aylantiriladi

### Context
- Har bir metod birinchi parametri `ctx context.Context`
- DB query larida context ishlatiladi: `pool.QueryRow(ctx, ...)`
- Background goroutine uchun `context.WithCancel` ishlatiladi

### Upsert mantiq (Paligon, Point)
```go
// id > 0 → UPDATE, id == 0 → INSERT
if req.Id > 0 {
    // UPDATE ... WHERE id = $1
} else {
    // INSERT ... RETURNING id
}
```

## Domain tushunchalari

| Term | Izoh |
|------|------|
| Paligon | Xodimlar ishlaydigan polygon hudud (boundary koordinatalar) |
| Point | Polygon ichidagi tashrif nuqtasi (radius metrda, ixtiyoriy vaqt oralig'i) |
| Duty | Ish smenasi: section + tashkilot + xodimlar + mashinalar |
| Assignment | Duty ichida: bir polygon + xodimlar + mashinalar guruhi |
| pinfl_hash | Xodimni identifikatsiya qiluvchi hash (64 belgi) |
| plateNumber | Mashinani identifikatsiya qiluvchi davlat raqami |
| Point Visit | Xodim/mashina nuqta radiusiga kirganini qayd etish (takrorlanmaydi) |

## Matematik algoritmlar

### Haversine (masofa hisoblash, metrda)
```go
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
```

### Ray Casting (nuqta polygon ichidami)
```go
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
```

## Vehicle Tracker (External HTTP)

**Endpoint:** `GET http://25.1.1.217:80/api/mobject/lastData`

**Response format:**
```json
{
  "result": [
    {
      "contractId": 1204,
      "mobjectId": 3938,
      "plateNumber": "01179VSC",
      "lat": 41.288,
      "lon": 69.201,
      "tpTimestamp": 1774939442050,
      "speed": 0,
      "movement": 0,
      "engineOn": 0
    }
  ],
  "error": null
}
```

**Ishlash tartibi:**
1. `duty_transports` jadvalidan aktiv duty lardagi `plate_number` larni ol
2. External API dan barcha mashinalar lokatsiyasini ol
3. `plateNumber` bo'yicha match qil
4. Match bo'lganlarni `vehicle_locations` ga yoz
5. Haversine + Ray Casting bilan point visit check qil
6. Har 30 soniyada takrorla (background goroutine)

## Database jadvallari

| Jadval | Maqsad |
|--------|--------|
| `paligons` | Polygon hududlar, boundary JSONB |
| `points` | Tashrif nuqtalari, paligon_id FK |
| `duties` | Ish smenalari |
| `duty_assignments` | Duty ↔ Paligon bog'lanish |
| `duty_employees` | Assignment ↔ pinfl_hash |
| `duty_transports` | Assignment ↔ plate_number |
| `locations` | Piyoda xodim GPS yozuvlari |
| `point_visits` | Nuqtaga tashrif (UNIQUE: pinfl+point+duty) |
| `vehicle_locations` | Mashina GPS yozuvlari |

### Muhim: duties jadvalidagi UNIQUE cheklovi

`section_id` uchun oddiy UNIQUE emas, **partial index** ishlatilsin:
```sql
CREATE UNIQUE INDEX duties_active_section_idx
    ON duties(section_id) WHERE ended_at IS NULL;
```
Bu eski to'xtatilgan dutylarni bloklamaydi.

## POINT_MISSED alarmi

Faqat `Location` RPC da tekshirish yetarli emas — xodim GPS yubormasa alarm ishlamaydi.
Shuning uchun **alohida ticker goroutine** kerak:
- Har N minutda aktiv duty larning barcha pointlarini tekshirsin
- `end_time` o'tgan, lekin `point_visits` da yozuv yo'q bo'lsa → `AlarmEvent{type:"POINT_MISSED"}` yuborsin

## AlarmStream — oneof subject

```proto
oneof subject {
  string pinfl_hash   = 9;
  string plate_number = 10;
}
```
Go generated kodida wrapper ishlatiladi:
```go
// Xodim uchun:
Event.Subject = &proto.AlarmEvent_PinflHash{PinflHash: "abc..."}
// Mashina uchun:
Event.Subject = &proto.AlarmEvent_PlateNumber{PlateNumber: "01A23BC"}
```

## Namuna request JSON lari

Namuna ma'lumotlar uchun `proto/proto uchun.json` faylini ko'r.

## Buyruqlar

```bash
# Proto generatsiya
protoc --go_out=. --go-grpc_out=. proto/location.proto

# Ishga tushirish
go run cmd/main.go

# Test
go test ./...

# Migration
psql $DATABASE_URL -f migrations/001_init.sql
```

## Environment variables

```env
GRPC_PORT=50051
DATABASE_URL=postgres://user:pass@localhost:5432/locationservice
VEHICLE_API_URL=http://25.1.1.217:80/api/mobject/lastData
VEHICLE_POLL_INTERVAL=30s
```
