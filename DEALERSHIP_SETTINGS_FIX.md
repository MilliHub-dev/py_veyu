# Dealership Settings Endpoint Fix

## Issue
The `/api/v1/admin/dealership/settings/` PUT endpoint was returning 400 errors due to two main problems:

1. **Services array being split into individual characters**: When services were provided as strings or in certain formats, the code was using `list(services)` which splits strings into characters instead of treating them as service names.
   - Example: `"Vehicle Delivery"` → `['V', 'e', 'h', 'i', 'c', 'l', 'e', ' ', 'D', 'e', 'l', 'i', 'v', 'e', 'r', 'y']`

2. **All fields marked as required**: The endpoint was enforcing required fields even though it should support partial updates.

## Changes Made

### 1. Fixed Services Parsing Logic (`listings/api/dealership_views.py`)

**Before:**
```python
else:
    # For any other type, try to convert to list
    logger.warning(f"Unexpected services type: {type(services)}, attempting conversion")
    try:
        services = list(services)  # ❌ This splits strings into characters!
    except (TypeError, ValueError):
        services = [str(services)]
```

**After:**
```python
else:
    # For any other type, wrap in a list (don't use list() which splits strings)
    logger.warning(f"Unexpected services type: {type(services)}, wrapping in list")
    services = [str(services)]  # ✅ Wraps the string in a list
```

### 2. Made All Fields Optional

**Before:**
```python
# Validate required fields first
required_fields = ['business_name', 'about', 'headline', 'services', 'contact_phone', 'contact_email']
missing_fields = [field for field in required_fields if field not in data or not data.get(field)]

if missing_fields:
    return Response({
        'error': True,
        'message': 'Missing required fields',
        ...
    }, status=400)
```

**After:**
```python
# Note: All fields are optional for partial updates
# Only validate fields that are provided
```

### 3. Updated Field Assignment Logic

Changed from always assigning fields to only updating provided fields:

**Before:**
```python
dealer.business_name = data['business_name']
dealer.about = data['about']
dealer.headline = data['headline']
# ... etc
```

**After:**
```python
if 'business_name' in data:
    dealer.business_name = data['business_name']
if 'about' in data:
    dealer.about = data['about']
if 'headline' in data:
    dealer.headline = data['headline']
# ... etc
```

### 4. Made Services Processing Optional

Services are now only processed if provided in the request:

```python
service_updates = None
if services is not None:
    # Process services...
    service_updates = service_processor.process_services(services)
else:
    logger.debug("No services provided in request, skipping service updates")
```

### 5. Updated API Documentation

Updated Swagger documentation to reflect that all fields are optional:

```python
@swagger_auto_schema(
    operation_summary="Update dealership settings",
    operation_description=(
        "Update dealership profile fields. All fields are optional - only provided fields will be updated.\n\n"
        ...
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        # removed: required=['business_name','about','headline','services','contact_phone','contact_email'],
        properties={
            ...
        }
    ),
    ...
)
```

## Testing

Run the test script to verify the fix:
```bash
python test_services_parsing.py
```

All tests should pass, showing that:
- Arrays of strings are handled correctly
- JSON string arrays are parsed properly
- Single service strings are wrapped in a list (not split into characters)

## API Usage

The endpoint now supports partial updates. You can send any combination of fields:

```javascript
// Update only services
PUT /api/v1/admin/dealership/settings/
{
  "services": ["Car Sale", "Vehicle Delivery"]
}

// Update only business name
PUT /api/v1/admin/dealership/settings/
{
  "business_name": "New Business Name"
}

// Update multiple fields
PUT /api/v1/admin/dealership/settings/
{
  "business_name": "ABC Motors",
  "services": ["Car Sale", "Motorbike Sales & Leasing", "Vehicle Delivery"],
  "headline": "Your trusted partner"
}
```

## Files Modified
- `listings/api/dealership_views.py` - Fixed services parsing and made fields optional
