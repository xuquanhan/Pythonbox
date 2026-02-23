---
name: "bloomberg-api-helper"
description: "Provides help documentation for Bloomberg BLPAPI Python. Invoke when user encounters issues with Bloomberg API, needs to troubleshoot blpapi errors, or asks for Bloomberg API usage examples."
---

# Bloomberg BLPAPI Python Helper

This skill provides help documentation and troubleshooting guidance for Bloomberg BLPAPI Python API.

## Documentation URL
https://bloomberg.github.io/blpapi-docs/python/3.26.1/

## Common Issues and Solutions

### Installation
```bash
python -m pip install --index-url=https://blpapi.bloomberg.com/repository/releases/python/simple blpapi
```

### Connection Setup
```python
import blpapi

# Setup connection options
options = blpapi.SessionOptions()
options.setServerHost("localhost")
options.setServerPort(8194)

# Create and start session
session = blpapi.Session(options)
session.start()
```

### Common Services
- `//blp/refdata` - Reference data (historical prices, fields)
- `//blp/mktdata` - Market data (real-time streaming)
- `//blp/apiflds` - API fields information
- `//blp/instruments` - Instrument lookup

### Request Types for Historical Data
```python
# Open reference data service
session.openService("//blp/refdata")
service = session.getService("//blp/refdata")

# Create historical data request
request = service.createRequest("HistoricalDataRequest")
request.getElement("securities").appendValue("AAPL US Equity")
request.getElement("fields").appendValue("PX_LAST")
request.set("periodicityAdjustment", "ACTUAL")
request.set("periodicitySelection", "DAILY")
request.set("startDate", "20230101")
request.set("endDate", "20231231")
```

### Error Handling
- **Connection refused**: Ensure Bloomberg Terminal is running
- **Limit reached**: Implement retry with backoff
- **Invalid security**: Check security identifier format

### Security Identifier Formats
- Equity: `AAPL US Equity`, `601989 CH Equity`
- Index: `SPX Index`
- Future: `ES1 Index`
- Option: `AAPL 01/19/24 C150 Equity`

## Troubleshooting Steps

1. **Check Bloomberg Terminal is running**
2. **Verify DAPI connection is active**
3. **Check firewall settings for port 8194**
4. **Review API limit usage**

## When to Use This Skill

Invoke this skill when:
- User reports Bloomberg API errors
- Need to look up BLPAPI documentation
- Troubleshooting connection issues
- Looking for code examples
- Understanding API limits and best practices
