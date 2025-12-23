# DataDome Scraper - 2025 December Edition

Bot scraping untuk bypass DataDome protection pada `bounty-nginx.datashield.co`.

## 2025 Features

- **JA4 Fingerprinting** (Chrome 131)
- **Activity Phases** (60-120s active, 5-12s rest)
- **Entropy >4.5 bits** (ML-resistant timing)
- **Nginx Timeout Exploitation** (50ms threshold)
- **Complete Chrome 131 Headers** (priority hints, zstd)

## Install

```bash
cd datadome-scraper
pip install -r requirements.txt
```

## Cara Dapat Cookie

1. Buka `https://bounty-nginx.datashield.co/scraping/0001` di Chrome
2. Selesaikan CAPTCHA jika muncul
3. DevTools (F12) > Application > Cookies
4. Copy value dari cookie `datadome`

## Usage

```bash
python main.py --cookie "PASTE_COOKIE_DISINI"
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--cookie`, `-c` | DataDome cookie (REQUIRED) | - |
| `--output`, `-o` | Output file | `results.json` |
| `--target`, `-t` | Target pages | 20000 |
| `--rps` | Target RPS | 12.0 |

## Output

```json
{
  "total": 20000,
  "blocked": false,
  "results": [
    {"path": "/scraping/0001", "hash": "abc123...", "status": 200}
  ]
}
```

## Report untuk Submission

```
Total scraped: 20000
Time taken: 1795.3s
Speed: 11.14 hits/sec
Entropy: 4.87 bits
Blocked: NO
```
