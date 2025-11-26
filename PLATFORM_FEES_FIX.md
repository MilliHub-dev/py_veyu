# Platform Fees Database Fix

## Problem
The `/api/v1/listings/checkout/` endpoint was returning a 500 error:
```
django.db.utils.ProgrammingError: relation "listings_platformfeesettings" does not exist
```

## Root Cause
1. Migration conflict: Two migrations numbered `0003_*` existed
2. The `PlatformFeeSettings` model existed in code but the database table wasn't created
3. Field name mismatch: migration used `date_updated` but model expected `last_updated`

## Solution Applied

### 1. Fixed Migration Conflicts
- Renamed `0003_platformfeesettings.py` to `0004_platformfeesettings.py`
- Updated dependency to point to `0003_boostpricing_listingboost_dealer_and_more`
- Fixed field definitions to match `DbModel` base class

### 2. Created Column Rename Migration
- Created `0005_rename_date_updated_to_last_updated.py` to fix field name mismatch

### 3. Applied Migrations
- Ran migrations on production database (Neon PostgreSQL)
- Created default `PlatformFeeSettings` record with:
  - Service Fee: 2% + ₦0
  - Inspection Fee: 5% (min: ₦10,000, max: ₦100,000)
  - Tax: 7.5%

## Verification
All tests passed:
- ✓ Active settings retrieved successfully
- ✓ Fee calculations working correctly
- ✓ Database table structure correct (12 columns)

## Files Created
- `run_migration.py` - Script to run migrations on production
- `run_migration.bat` - Windows batch file for easy execution
- `create_default_fee_settings.py` - Script to create default settings
- `verify_platform_fees.py` - Verification script

## Next Steps
The checkout endpoint should now work correctly. The error was caused by missing database table, which has been created and populated with default settings.
