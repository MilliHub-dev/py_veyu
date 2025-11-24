# Form URL Encoded Content Type Fix

## Issue
The `/api/v1/admin/dealership/listings/create/` endpoint was returning a 500 error with:
```
rest_framework.exceptions.UnsupportedMediaType: Unsupported media type "application/x-www-form-urlencoded" in request.
```

## Root Cause
The `CreateListingView`, `ListingDetailView`, and `SettingsView` classes only had `MultiPartParser` and `JSONParser` in their `parser_classes`, which meant they only accepted:
- `multipart/form-data` (for file uploads)
- `application/json` (for JSON data)

They did **not** accept `application/x-www-form-urlencoded`, which is the default content type for HTML forms and some API clients.

## Solution
Added `FormParser` to the `parser_classes` for the following views:
1. `CreateListingView` - for creating listings
2. `ListingDetailView` - for editing listings
3. `SettingsView` - for updating dealership settings

### Changes Made
```python
from rest_framework.parsers import (
    MultiPartParser,
    JSONParser,
    FormParser,  # Added
)

class CreateListingView(CreateAPIView):
    parser_classes = [MultiPartParser, JSONParser, FormParser]  # Added FormParser
    # ...

class ListingDetailView(RetrieveUpdateDestroyAPIView):
    parser_classes = [MultiPartParser, JSONParser, FormParser]  # Added FormParser
    # ...

class SettingsView(APIView):
    parser_classes = [MultiPartParser, JSONParser, FormParser]  # Added FormParser
    # ...
```

## Impact
- The endpoints now accept all three common content types:
  - `application/json` - JSON data
  - `multipart/form-data` - File uploads with form data
  - `application/x-www-form-urlencoded` - Standard HTML form submissions
- No breaking changes - existing clients using JSON or multipart will continue to work
- Fixes compatibility with clients that default to form-urlencoded content type

## Testing
Test the endpoint with form-urlencoded data:
```bash
curl -X POST http://localhost:8000/api/v1/admin/dealership/listings/create/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "action=create-listing&title=Test+Car&brand=Toyota&model=Camry&..."
```

## Date Fixed
November 24, 2025
