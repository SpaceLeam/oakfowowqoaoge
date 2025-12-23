# DataDome Scraper - Bug Bounty Tool

Bot scraping untuk bypass DataDome protection pada `bounty-nginx.datashield.co`.

## Target
- **Medium Scenario**: 20,000 pages dalam 30 menit (~12 RPS)

## Install

```bash
cd datadome-scraper
pip install -r requirements.txt
```

## Cara Dapat Cookie

1. Buka `https://bounty-nginx.datashield.co/scraping/0001` di browser (Chrome recommended)
2. Selesaikan CAPTCHA jika muncul
3. Buka DevTools (F12) > Application > Cookies
4. Copy **value** dari cookie `datadome`

## Usage

```bash
python main.py --cookie "PASTE_COOKIE_VALUE_DISINI"
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--cookie`, `-c` | DataDome cookie value (REQUIRED) | - |
| `--output`, `-o` | Output file untuk results | `results.json` |
| `--target`, `-t` | Target jumlah pages | 20000 |
| `--rps` | Target requests per second | 12.0 |

### Examples

```bash
# Medium scenario (default)
python main.py -c "eyJjYWxsZWQi..." -o medium_results.json

# Custom target
python main.py -c "eyJjYWxsZWQi..." --target 5000 --rps 8
```

## Output

File `results.json` berisi:
```json
{
  "total": 20000,
  "blocked": false,
  "results": [
    {"path": "/scraping/0001", "hash": "abc123...", "status": 200},
    ...
  ]
}
```

## Bypass Techniques Used

1. **TLS Fingerprinting**: Chrome 131 JA4 fingerprint via `tls-client`
2. **Burst Pattern**: 20-30 requests cepat, lalu pause
3. **Cooldown**: Pause 4-8 detik setiap ~500 requests
4. **Timing Variance**: >15% variance untuk evade ML detection
5. **Cookie Rotation**: Auto-update cookie dari response headers

## Report untuk Submission

Setelah run, akan muncul summary:
```
Total scraped: 20000
Time taken: 1795.3s
Speed: 11.14 hits/sec
Blocked: NO
```

Gunakan data ini + file `results.json` untuk submission.
