# Business Verification API Documentation

## Overview
The Business Verification system allows dealers and mechanics to submit their business details for manual admin approval. This replaces the previous Dojah integration with a more controlled verification process.

## Base URL
```
https://dev.veyu.cc/api/v1/accounts/
```

## Authentication
All endpoints require authentication via:
- **Token Authentication**: `Authorization: Token <your_token>`
- **JWT Authentication**: `Authorization: Bearer <your_jwt_token>`

Only users with `user_type` of `dealer` or `mechanic` can access these endpoints.

---

## Endpoints

### 1. Check Verification Status

**GET** `/verify-business/`

Check the current business verification status for the authenticated user.

#### Request Headers
```http
Authorization: Bearer <your_token>
```

#### Response - Success (200 OK)

**Not Submitted:**
```json
{
  "status": "not_submitted",
  "status_display": "Not Submitted",
  "submission_date": null,
  "rejection_reason": null
}
```

**Pending Review:**
```json
{
  "status": "pending",
  "status_display": "Pending Review",
  "submission_date": "2025-10-20T14:30:00Z",
  "rejection_reason": null
}
```

**Verified:**
```json
{
  "status": "verified",
  "status_display": "Verified",
  "submission_date": "2025-10-20T14:30:00Z",
  "rejection_reason": null
}
```

**Rejected:**
```json
{
  "status": "rejected",
  "status_display": "Rejected",
  "submission_date": "2025-10-20T14:30:00Z",
  "rejection_reason": "Please provide a valid CAC certificate. The document submitted is not readable."
}
```

#### Response - Error (400 Bad Request)
```json
{
  "error": true,
  "message": "Only dealers and mechanics can submit business verification"
}
```

#### Response - Error (404 Not Found)
```json
{
  "error": true,
  "message": "Business profile not found"
}
```

---

### 2. Submit Business Verification

**POST** `/verify-business/`

Submit business verification details for admin review. If a submission already exists, it will be updated and status reset to `pending`.

#### Request Headers
```http
Authorization: Bearer <your_token>
Content-Type: multipart/form-data
```

#### Request Body (Form Data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `business_type` | string | **Yes** | Either `"dealership"` or `"mechanic"` |
| `business_name` | string | **Yes** | Official registered business name |
| `business_address` | string | **Yes** | Full business address |
| `business_email` | string | **Yes** | Business contact email |
| `business_phone` | string | **Yes** | Business contact phone (format: +234...) |
| `cac_number` | string | No | Corporate Affairs Commission number (e.g., RC123456) |
| `tin_number` | string | No | Tax Identification Number (e.g., 12345678-0001) |
| `cac_document` | file | No | CAC registration certificate (PDF, JPG, PNG) |
| `tin_document` | file | No | TIN certificate (PDF, JPG, PNG) |
| `proof_of_address` | file | No | Utility bill or lease agreement (PDF, JPG, PNG) |
| `business_license` | file | No | Business operating license (PDF, JPG, PNG) |

#### Example Request (JavaScript/Fetch)
```javascript
const formData = new FormData();
formData.append('business_type', 'dealership');
formData.append('business_name', 'ABC Motors Limited');
formData.append('cac_number', 'RC123456');
formData.append('tin_number', '12345678-0001');
formData.append('business_address', '123 Main Street, Victoria Island, Lagos');
formData.append('business_email', 'info@abcmotors.com');
formData.append('business_phone', '+2348012345678');
formData.append('cac_document', cacFileInput.files[0]);
formData.append('tin_document', tinFileInput.files[0]);
formData.append('proof_of_address', addressFileInput.files[0]);
formData.append('business_license', licenseFileInput.files[0]);

const response = await fetch('https://dev.veyu.cc/api/v1/accounts/verify-business/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const data = await response.json();
```

#### Response - Success (201 Created)
```json
{
  "error": false,
  "message": "Business verification submitted successfully. Admin will review your submission.",
  "data": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "business_type": "dealership",
    "status": "pending",
    "business_name": "ABC Motors Limited",
    "cac_number": "RC123456",
    "tin_number": "12345678-0001",
    "business_address": "123 Main Street, Victoria Island, Lagos",
    "business_email": "info@abcmotors.com",
    "business_phone": "+2348012345678",
    "cac_document": "/media/verification/cac/document.pdf",
    "tin_document": "/media/verification/tin/document.pdf",
    "proof_of_address": "/media/verification/address/document.pdf",
    "business_license": "/media/verification/license/document.pdf",
    "rejection_reason": null,
    "date_created": "2025-10-20T14:30:00Z",
    "last_updated": "2025-10-20T14:30:00Z",
    "business_verification_status": "Pending Review"
  }
}
```

#### Response - Error (400 Bad Request)
```json
{
  "error": true,
  "message": "Validation failed",
  "errors": {
    "business_name": ["This field is required."],
    "business_email": ["Enter a valid email address."]
  }
}
```

---

### 3. Login Response Enhancement

**POST** `/login/`

The login endpoint now includes `business_verification_status` for dealers and mechanics.

#### Response Example (Dealer)
```json
{
  "id": 123,
  "email": "dealer@example.com",
  "token": "abc123token",
  "refresh": "refresh_token_here",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "dealer",
  "provider": "veyu",
  "is_active": true,
  "dealerId": "550e8400-e29b-41d4-a716-446655440000",
  "verified_id": true,
  "verified_business": false,
  "business_verification_status": "pending"
}
```

#### Response Example (Mechanic)
```json
{
  "id": 456,
  "email": "mechanic@example.com",
  "token": "xyz789token",
  "refresh": "refresh_token_here",
  "first_name": "Jane",
  "last_name": "Smith",
  "user_type": "mechanic",
  "provider": "veyu",
  "is_active": true,
  "mechanicId": "660e8400-e29b-41d4-a716-446655440001",
  "verified_id": true,
  "verified_business": true,
  "business_verification_status": "verified"
}
```

---

## Verification Status Flow

```
┌─────────────────┐
│  not_submitted  │  ← Initial state (no submission yet)
└────────┬────────┘
         │
         │ User submits form
         ↓
┌─────────────────┐
│     pending     │  ← Awaiting admin review
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         │ Admin approves  │ Admin rejects
         ↓                 ↓
┌─────────────────┐  ┌─────────────────┐
│    verified     │  │    rejected     │
└─────────────────┘  └────────┬────────┘
                              │
                              │ User resubmits
                              ↓
                     ┌─────────────────┐
                     │     pending     │
                     └─────────────────┘
```

---

## Status Values

| Status | Display | Description |
|--------|---------|-------------|
| `not_submitted` | Not Submitted | User hasn't submitted verification yet |
| `pending` | Pending Review | Submitted and waiting for admin approval |
| `verified` | Verified | Approved by admin - business is verified |
| `rejected` | Rejected | Rejected by admin - check `rejection_reason` |

---

## Frontend Implementation Guide

### 1. Check Status on Login
```javascript
// After successful login
if (userData.user_type === 'dealer' || userData.user_type === 'mechanic') {
  const verificationStatus = userData.business_verification_status;
  
  switch(verificationStatus) {
    case 'not_submitted':
      // Show "Complete Verification" button/banner
      break;
    case 'pending':
      // Show "Verification Pending" status badge
      break;
    case 'verified':
      // Show verified badge/checkmark
      break;
    case 'rejected':
      // Show rejection message and "Resubmit" button
      break;
  }
}
```

### 2. Verification Form Component
```javascript
const VerificationForm = () => {
  const [formData, setFormData] = useState({
    business_type: 'dealership', // or 'mechanic'
    business_name: '',
    cac_number: '',
    tin_number: '',
    business_address: '',
    business_email: '',
    business_phone: '',
  });
  
  const [files, setFiles] = useState({
    cac_document: null,
    tin_document: null,
    proof_of_address: null,
    business_license: null,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formDataToSend = new FormData();
    
    // Append text fields
    Object.keys(formData).forEach(key => {
      formDataToSend.append(key, formData[key]);
    });
    
    // Append files
    Object.keys(files).forEach(key => {
      if (files[key]) {
        formDataToSend.append(key, files[key]);
      }
    });
    
    try {
      const response = await fetch('/api/v1/accounts/verify-business/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formDataToSend
      });
      
      const data = await response.json();
      
      if (data.error) {
        // Handle validation errors
        console.error(data.errors);
      } else {
        // Success - show confirmation
        alert(data.message);
      }
    } catch (error) {
      console.error('Submission failed:', error);
    }
  };
  
  // ... render form
};
```

### 3. Status Check Component
```javascript
const VerificationStatus = () => {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    const fetchStatus = async () => {
      const response = await fetch('/api/v1/accounts/verify-business/', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setStatus(data);
    };
    
    fetchStatus();
  }, []);
  
  if (!status) return <div>Loading...</div>;
  
  return (
    <div className={`status-badge status-${status.status}`}>
      <span>{status.status_display}</span>
      {status.rejection_reason && (
        <p className="rejection-reason">{status.rejection_reason}</p>
      )}
    </div>
  );
};
```

### 4. Status Badge Styling
```css
.status-badge {
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 600;
}

.status-not_submitted {
  background-color: #f3f4f6;
  color: #6b7280;
}

.status-pending {
  background-color: #fef3c7;
  color: #d97706;
}

.status-verified {
  background-color: #d1fae5;
  color: #059669;
}

.status-rejected {
  background-color: #fee2e2;
  color: #dc2626;
}
```

---

## Error Handling

### Common Errors

1. **401 Unauthorized**
   - Token expired or invalid
   - Action: Redirect to login

2. **400 Bad Request**
   - Validation errors
   - Action: Display field-specific errors to user

3. **404 Not Found**
   - Business profile doesn't exist
   - Action: Contact support (shouldn't happen in normal flow)

### Example Error Handler
```javascript
const handleApiError = (response, data) => {
  switch(response.status) {
    case 400:
      // Show validation errors
      if (data.errors) {
        Object.keys(data.errors).forEach(field => {
          showFieldError(field, data.errors[field][0]);
        });
      }
      break;
    case 401:
      // Redirect to login
      window.location.href = '/login';
      break;
    case 404:
      alert('Business profile not found. Please contact support.');
      break;
    default:
      alert('An error occurred. Please try again.');
  }
};
```

---

## Testing

### Test Accounts
- **Dealer**: `dealer@test.com` / `password123`
- **Mechanic**: `mechanic@test.com` / `password123`

### Swagger UI
Access interactive API documentation at:
```
https://dev.veyu.cc/swagger/
```

### Test Workflow
1. Login as dealer/mechanic
2. Check status (should be `not_submitted`)
3. Submit verification form
4. Check status (should be `pending`)
5. Admin approves/rejects in admin panel
6. Check status again (should be `verified` or `rejected`)

---

## Notes

- **File Size Limits**: Max 5MB per file (configurable in backend)
- **Supported Formats**: PDF, JPG, JPEG, PNG
- **Resubmission**: Users can resubmit after rejection (status resets to `pending`)
- **Admin Panel**: Admins can view, approve, or reject submissions at `/admin/accounts/businessverificationsubmission/`

---

## Support

For questions or issues, contact the backend team or check the Swagger documentation at `/swagger/`.
