# Inspection Slip Error Fix

## Problem
The API endpoint `/api/v1/inspections/slips/INSP-8/` was returning a 500 error with the message:
```
ERROR: No VehicleInspection matches the given query.
```

## Root Causes

### 1. Non-existent Inspection
- The user was trying to access inspection slip "INSP-8" which doesn't exist in the database
- Only 1 inspection exists (ID: 1) with inspection number "INSP-1"

### 2. Missing Inspection Numbers (Data Integrity Issue)
- Inspection ID 1 was marked as paid but had no `inspection_number` generated
- This was likely due to the inspection being created before the `mark_paid()` method was properly implemented

### 3. Incorrect Related Name References
- The code was using `hasattr(user, 'customer')` but the actual related name is `customer_profile`
- The code was using `hasattr(user, 'dealership')` but the actual related name is `dealership_profile`
- This was causing permission checks to fail even for authorized users

### 4. Incorrect Vehicle Model Fields
- The code was referencing `vehicle.make` and `vehicle.year` which don't exist
- The actual fields are `vehicle.brand` and no year field exists
- The code was referencing `user.phone_number` but phone is on the profile, not the Account model

## Solutions Applied

### 1. Fixed Existing Data
Created and ran `fix_inspection_numbers.py` to:
- Find all paid inspections without inspection numbers
- Generate proper inspection numbers for them
- Result: Inspection ID 1 now has inspection_number "INSP-1"

### 2. Improved Error Handling
Updated `InspectionSlipRetrievalView` in `inspections/views.py`:
- Changed from `get_object_or_404()` to explicit try/except with `DoesNotExist`
- Now returns proper 404 response with clear error message
- Added `success: false` flag to error responses
- Improved error messages for better user experience

**Before:**
```python
inspection = get_object_or_404(VehicleInspection, inspection_number=slip_number)
# Returns generic 500 error
```

**After:**
```python
try:
    inspection = VehicleInspection.objects.get(inspection_number=slip_number)
except VehicleInspection.DoesNotExist:
    return Response({
        'success': False,
        'error': 'Inspection slip not found',
        'message': f'No inspection found with slip number "{slip_number}". Please verify the slip number and try again.'
    }, status=status.HTTP_404_NOT_FOUND)
```

### 3. Fixed Permission Checks Throughout inspections/views.py
Updated all permission checks to use correct related names:
- Changed `hasattr(user, 'customer')` → `hasattr(user, 'customer_profile')`
- Changed `user.customer` → `user.customer_profile`
- Changed `hasattr(user, 'dealership')` → `hasattr(user, 'dealership_profile')`
- Changed `user.dealership` → `user.dealership_profile`

This affects multiple views:
- `VehicleInspectionListCreateView`
- `VehicleInspectionDetailView`
- `InspectionPhotoUploadView`
- `DocumentGenerationView`
- `DocumentPreviewView`
- `DocumentDownloadView`
- `InspectionStatsView`
- `InspectionSlipRetrievalView`
- `InspectionSlipVerificationView`
- `pay_for_inspection`
- `verify_inspection_payment`
- `regenerate_inspection_slip`

### 4. Fixed Model Field References
Updated vehicle and user data serialization:
- Changed `vehicle.make` → `vehicle.brand`
- Removed reference to non-existent `vehicle.year`
- Added `vehicle.condition` and `vehicle.color`
- Changed `user.phone_number` → `customer.phone_number` (from profile)
- Changed `dealer.user.phone_number` → `dealer.phone_number` (from profile)

## Current Database State
- Total inspections: 1
- Inspection ID 1:
  - Inspection Number: INSP-1
  - Status: Draft
  - Payment Status: Paid
  - Vehicle: toyota

## Testing
Comprehensive tests were run to verify the fixes:

### Test Results
1. **Valid slip with correct user**: `GET /api/v1/inspections/slips/INSP-1/` as customer
   - ✓ Returns 200 with full inspection details
   - ✓ Permission check works correctly
   
2. **Valid slip with wrong user**: `GET /api/v1/inspections/slips/INSP-1/` as different user
   - ✓ Returns 403 with permission denied message
   
3. **Invalid slip**: `GET /api/v1/inspections/slips/INSP-8/`
   - ✓ Returns 404 with clear error message
   - ✓ Includes `success: false` flag
   - ✓ Provides helpful message to user

### Test Scripts Created
- `diagnose_inspection.py` - Diagnostic tool to check inspection data
- `fix_inspection_numbers.py` - One-time fix for missing inspection numbers
- `test_inspection_slip_fix.py` - Automated tests for the endpoint
- `test_with_correct_user.py` - Test with authorized user
- `debug_permissions.py` - Debug permission checking
- `check_related_name.py` - Verify related name usage

## Prevention
The `mark_paid()` method in `VehicleInspection` model already has logic to generate inspection numbers:
```python
def mark_paid(self, transaction, payment_method='wallet'):
    # ... payment logic ...
    
    # Generate inspection number if not exists
    if not self.inspection_number:
        self.inspection_number = self._generate_inspection_number()
    
    self.save()
```

This ensures all future paid inspections will have proper inspection numbers.

## Files Modified
1. `inspections/views.py` - Improved error handling in `InspectionSlipRetrievalView`
2. `fix_inspection_numbers.py` - One-time fix script (can be deleted after deployment)
3. `diagnose_inspection.py` - Diagnostic script (can be kept for future debugging)
