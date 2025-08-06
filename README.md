# FastAPI Job Scraper

A robust FastAPI application for scraping job postings from Indeed and LinkedIn using Playwright browser automation with anti-detection measures.

## Features

- **Indeed Scraping**: Scrape job listings from Indeed.com
- **LinkedIn Scraping**: Scrape job listings from LinkedIn.com with optional login
- **Excel Export**: Download scraped data as formatted Excel files
- **Anti-Detection**: Built-in stealth measures to avoid bot detection
- **Async Processing**: Full async/await support for better performance
- **Error Handling**: Comprehensive error handling and logging
- **Rate Limiting**: Built-in delays and random intervals
- **CAPTCHA Detection**: Basic CAPTCHA and security challenge detection

## Architecture

```
scrapper/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── scrapers/              # Scraper modules
│   ├── __init__.py
│   ├── indeed_scraper.py  # Indeed.com scraper
│   └── linkedin_scraper.py # LinkedIn.com scraper
└── utils/                 # Utility modules
    ├── __init__.py
    └── browser_manager.py # Browser management and anti-detection
```

## Setup Instructions

### 1. Install Dependencies

**Option A: Automated Setup (Recommended)**
```bash
# Use the automated startup script (creates venv automatically)
./start.sh
```

**Option B: Manual Virtual Environment Setup**
```bash
# Create and setup virtual environment
./setup_venv.sh

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not using setup script)
pip install -r requirements.txt

# ChromeDriver will be automatically managed by webdriver-manager
```

**Option C: Manual Setup (No Virtual Environment)**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Environment Variables (Optional)

Create a `.env` file in the project root for LinkedIn login credentials:

```env
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

**Note**: LinkedIn scraping works without login but may have limited results.

### 3. Run the Application

**If using virtual environment:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

**If not using virtual environment:**
```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint
- **GET** `/` - API information and available endpoints

### Health Check
- **GET** `/health` - Health check endpoint

### Indeed Scraping
- **GET** `/scrape/indeed` - Scrape job postings from Indeed (JSON response)
- **GET** `/scrape/indeed/excel` - Scrape job postings from Indeed and download as Excel file

**Query Parameters:**
- `job` (required): Job title to search for
- `location` (required): Job location
- `max_jobs` (optional): Maximum number of jobs to scrape (default: 10, max: 50)

**Examples:**
```bash
# JSON response
curl "http://localhost:8000/scrape/indeed?job=python+developer&location=remote&max_jobs=5"

# Excel download
curl "http://localhost:8000/scrape/indeed/excel?job=python+developer&location=remote&max_jobs=5" -o jobs.xlsx
```

### LinkedIn Scraping
- **GET** `/scrape/linkedin` - Scrape job postings from LinkedIn (JSON response)
- **GET** `/scrape/linkedin/excel` - Scrape job postings from LinkedIn and download as Excel file

**Query Parameters:**
- `job` (required): Job title to search for
- `location` (required): Job location
- `max_jobs` (optional): Maximum number of jobs to scrape (default: 10, max: 50)

**Examples:**
```bash
# JSON response
curl "http://localhost:8000/scrape/linkedin?job=python+developer&location=remote&max_jobs=5"

# Excel download
curl "http://localhost:8000/scrape/linkedin/excel?job=python+developer&location=remote&max_jobs=5" -o jobs.xlsx
```

### Export Management
- **GET** `/exports` - List all exported Excel files
- **GET** `/exports/{filename}` - Download a specific exported Excel file

**Examples:**
```bash
# List all exports
curl "http://localhost:8000/exports"

# Download specific file
curl "http://localhost:8000/exports/linkedin_python_remote_20241201_143022.xlsx" -o downloaded_file.xlsx
```

## Response Format

All scraping endpoints return a consistent JSON response:

```json
{
  "success": true,
  "message": "Successfully scraped 5 jobs from Indeed",
  "jobs": [
    {
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "Remote",
      "url": "https://indeed.com/viewjob?jk=123456"
    }
  ],
  "total_count": 5
}
```

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def scrape_jobs():
    async with httpx.AsyncClient() as client:
        # Scrape Indeed
        response = await client.get(
            "http://localhost:8000/scrape/indeed",
            params={
                "job": "python developer",
                "location": "remote",
                "max_jobs": 10
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['total_count']} jobs on Indeed")
            for job in data['jobs']:
                print(f"- {job['title']} at {job['company']} ({job['location']})")

# Run the example
asyncio.run(scrape_jobs())
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

async function scrapeJobs() {
    try {
        const response = await axios.get('http://localhost:8000/scrape/linkedin', {
            params: {
                job: 'python developer',
                location: 'remote',
                max_jobs: 10
            }
        });
        
        console.log(`Found ${response.data.total_count} jobs on LinkedIn`);
        response.data.jobs.forEach(job => {
            console.log(`- ${job.title} at ${job.company} (${job.location})`);
        });
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

scrapeJobs();
```

## Anti-Detection Features

The application includes several measures to avoid bot detection:

### Browser Configuration
- Custom user agent strings
- Realistic viewport settings
- Disabled automation indicators
- Stealth JavaScript injection

### Behavioral Patterns
- Random delays between actions
- Human-like scrolling patterns
- Network idle waiting
- Realistic mouse movements

### Headers and Cookies
- Proper HTTP headers
- Session management
- Cookie handling

## Error Handling

The application handles various error scenarios:

- **Network Timeouts**: Configurable timeout settings
- **CAPTCHA Detection**: Automatic detection and error reporting
- **Rate Limiting**: Built-in delays and retry logic
- **Invalid Selectors**: Fallback selectors for different page layouts
- **Login Failures**: Graceful handling of authentication issues

## Advanced Configuration

### Browser Settings

You can modify browser settings in `utils/browser_manager.py`:

```python
# Launch options
self.browser = await self.playwright.chromium.launch(
    headless=True,  # Set to False for debugging
    args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        # Add more arguments as needed
    ]
)
```

### Proxy Support

To add proxy support, modify the browser launch in `utils/browser_manager.py`:

```python
# Add proxy configuration
self.browser = await self.playwright.chromium.launch(
    proxy={
        "server": "http://proxy-server:port",
        "username": "username",
        "password": "password"
    }
)
```

### Custom Delays

Adjust scraping delays in the scraper classes:

```python
# In scrapers/indeed_scraper.py or scrapers/linkedin_scraper.py
await self.browser_manager.add_random_delay(2, 4)  # 2-4 second delay
```

## Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   # If playwright install fails
   pip install playwright
   playwright install chromium
   ```

2. **Permission Errors**
   ```bash
   # On Linux/macOS, ensure proper permissions
   chmod +x ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome
   ```

3. **LinkedIn Login Issues**
   - Ensure credentials are correct
   - Check for 2FA requirements
   - Try without login first

4. **No Jobs Found**
   - Verify search parameters
   - Check if selectors need updating
   - Try different job titles/locations

### Debug Mode

Enable debug mode by setting `headless=False` in `utils/browser_manager.py`:

```python
self.browser = await self.playwright.chromium.launch(
    headless=False,  # Shows browser window
    # ... other options
)
```

## Performance Optimization

### Scaling Considerations

- **Concurrent Requests**: Limit concurrent scraping requests
- **Resource Management**: Proper browser cleanup
- **Caching**: Implement result caching for repeated queries
- **Rate Limiting**: Respect website rate limits

### Monitoring

Monitor the application logs for:
- Scraping success rates
- Error patterns
- Performance metrics
- CAPTCHA detection frequency

## Security Considerations

- **Credentials**: Store LinkedIn credentials securely
- **Rate Limiting**: Implement proper rate limiting
- **User Input**: Validate and sanitize all inputs
- **Error Messages**: Avoid exposing sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational purposes. Please respect the terms of service of the websites you're scraping.

## Disclaimer

This tool is for educational and research purposes only. Users are responsible for complying with the terms of service of the websites they scrape. The authors are not responsible for any misuse of this software. 