# Vehicle Inspection System - Frontend Implementation Guide

## Overview

This guide covers the complete inspection flow from payment to document signing for frontend implementation.

## Table of Contents

1. [Complete Flow Overview](#complete-flow-overview)
2. [API Endpoints Reference](#api-endpoints-reference)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Payment Integration](#payment-integration)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [UI/UX Recommendations](#uiux-recommendations)

---

## Complete Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSPECTION COMPLETE FLOW                      │
└─────────────────────────────────────────────────────────────────┘

Step 1: GET FEE QUOTE (Optional)
   ↓
Step 2: CREATE INSPECTION
   ↓
Step 3: PAY FOR INSPECTION (Wallet or Bank)
   ↓
Step 4: CONDUCT INSPECTION (Inspector)
   ↓
Step 5: COMPLETE INSPECTION
   ↓
Step 6: GENERATE DOCUMENT
   ↓
Step 7: SIGN DOCUMENT (All Parties)
   ↓
Step 8: DOWNLOAD SIGNED DOCUMENT
```

---

## API Endpoints Reference

### Base URL
```
Production: https://veyu.cc/api/v1
Staging: https://staging.veyu.cc/api/v1
```

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

### Endpoints Summary

| Step | Method | Endpoint | Purpose |
|------|--------|----------|---------|
| 1 | POST | `/inspections/quote/` | Get fee quote |
| 2 | POST | `/inspections/` | Create inspection |
| 3a | POST | `/inspections/{id}/pay/` | Pay (wallet/bank) |
| 3b | POST | `/inspections/{id}/verify-payment/` | Verify Paystack |
| 4 | GET | `/inspections/{id}/` | Get inspection details |
| 4 | POST | `/inspections/{id}/photos/` | Upload photos |
| 5 | POST | `/inspections/{id}/complete/` | Mark complete |
| 6 | POST | `/inspections/{id}/generate-document/` | Generate PDF |
| 7 | GET | `/inspections/documents/{doc_id}/preview/` | Preview document |
| 7 | POST | `/inspections/documents/{doc_id}/sign/` | Submit signature |
| 8 | GET | `/inspections/documents/{doc_id}/download/` | Download PDF |

---


## Step-by-Step Implementation

### STEP 1: Get Fee Quote (Optional)

**Purpose:** Show customer the inspection fee before creating the inspection.

**Endpoint:** `POST /api/v1/inspections/quote/`

**Request:**
```json
{
  "inspection_type": "pre_purchase",
  "vehicle_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "inspection_type": "pre_purchase",
    "base_fee": 50000.00,
    "vehicle_info": {
      "id": 123,
      "name": "Toyota Camry 2020",
      "brand": "Toyota",
      "model": "Camry"
    },
    "total_fee": 50000.00,
    "currency": "NGN"
  },
  "message": "Fee quote generated successfully"
}
```

**Frontend Implementation:**
```javascript
async function getInspectionQuote(inspectionType, vehicleId = null) {
  const response = await fetch('/api/v1/inspections/quote/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      inspection_type: inspectionType,
      vehicle_id: vehicleId
    })
  });
  
  const data = await response.json();
  return data;
}
```

**UI Display:**
```
┌─────────────────────────────────────┐
│  Inspection Fee Quote               │
├─────────────────────────────────────┤
│  Type: Pre-Purchase Inspection      │
│  Vehicle: Toyota Camry 2020         │
│  Fee: ₦50,000.00                    │
│                                     │
│  [Continue to Book]                 │
└─────────────────────────────────────┘
```

---

### STEP 2: Create Inspection

**Purpose:** Create the inspection record with pending payment status.

**Endpoint:** `POST /api/v1/inspections/`

**Request:**
```json
{
  "vehicle": 123,
  "inspector": 456,
  "customer": 789,
  "dealer": 101,
  "inspection_type": "pre_purchase"
}
```

**Response:**
```json
{
  "id": 1,
  "vehicle_name": "Toyota Camry 2020",
  "inspector_name": "John Mechanic",
  "customer_name": "Jane Customer",
  "dealer_name": "AutoHub Motors",
  "inspection_type": "pre_purchase",
  "inspection_type_display": "Pre-Purchase Inspection",
  "status": "pending_payment",
  "status_display": "Pending Payment",
  "payment_status": "unpaid",
  "payment_status_display": "Unpaid",
  "inspection_fee": 50000.00,
  "inspection_date": "2024-01-15T10:00:00Z",
  "paid_at": null,
  "completed_at": null
}
```

**Frontend Implementation:**
```javascript
async function createInspection(inspectionData) {
  const response = await fetch('/api/v1/inspections/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(inspectionData)
  });
  
  const data = await response.json();
  return data;
}
```

---


### STEP 3: Pay for Inspection

#### Option A: Wallet Payment (Instant)

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/pay/`

**Request:**
```json
{
  "payment_method": "wallet",
  "amount": 50000.00
}
```

**Response (Success):**
```json
{
  "success": true,
  "data": {
    "inspection_id": 1,
    "transaction_id": 789,
    "amount_paid": 50000.00,
    "payment_method": "wallet",
    "payment_status": "paid",
    "inspection_status": "Draft",
    "paid_at": "2024-01-15T10:30:00Z",
    "remaining_balance": 450000.00
  },
  "message": "Payment successful. Inspection can now begin."
}
```

**Response (Insufficient Balance):**
```json
{
  "error": "Insufficient wallet balance",
  "available_balance": 30000.00,
  "required_amount": 50000.00
}
```

**Frontend Implementation:**
```javascript
async function payWithWallet(inspectionId, amount) {
  try {
    const response = await fetch(`/api/v1/inspections/${inspectionId}/pay/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_method: 'wallet',
        amount: amount
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Payment successful - redirect to inspection page
      window.location.href = `/inspections/${inspectionId}`;
    } else {
      // Show error
      alert(data.error);
    }
  } catch (error) {
    console.error('Payment failed:', error);
  }
}
```

---

#### Option B: Bank Payment (Paystack)

**Step 3b.1: Initiate Payment**

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/pay/`

**Request:**
```json
{
  "payment_method": "bank",
  "amount": 50000.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payment_method": "bank",
    "amount": 50000.00,
    "inspection_id": 1,
    "transaction_id": 789,
    "reference": "veyu-inspection-1-abc123def456",
    "email": "customer@example.com",
    "currency": "NGN",
    "callback_url": "https://veyu.cc/api/v1/inspections/1/verify-payment/"
  },
  "message": "Initialize Paystack payment on frontend with the provided reference"
}
```

**Step 3b.2: Open Paystack Checkout**

**Frontend Implementation:**
```javascript
// Include Paystack script in HTML
// <script src="https://js.paystack.co/v1/inline.js"></script>

async function payWithBank(inspectionId, amount) {
  try {
    // 1. Initiate payment
    const response = await fetch(`/api/v1/inspections/${inspectionId}/pay/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_method: 'bank',
        amount: amount
      })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      alert(data.error);
      return;
    }
    
    // 2. Open Paystack popup
    const paystack = PaystackPop.setup({
      key: 'YOUR_PAYSTACK_PUBLIC_KEY',
      email: data.data.email,
      amount: data.data.amount * 100, // Convert to kobo
      ref: data.data.reference,
      currency: data.data.currency,
      
      onSuccess: async (transaction) => {
        console.log('Payment successful:', transaction);
        // 3. Verify payment
        await verifyPayment(inspectionId, transaction.reference);
      },
      
      onCancel: () => {
        alert('Payment cancelled');
      }
    });
    
    paystack.openIframe();
    
  } catch (error) {
    console.error('Payment error:', error);
  }
}
```

**Step 3b.3: Verify Payment**

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/verify-payment/`

**Request:**
```json
{
  "reference": "veyu-inspection-1-abc123def456"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "inspection_id": 1,
    "transaction_id": 789,
    "amount_paid": 50000.00,
    "payment_method": "bank",
    "payment_status": "paid",
    "inspection_status": "Draft",
    "paid_at": "2024-01-15T10:30:00Z",
    "reference": "veyu-inspection-1-abc123def456"
  },
  "message": "Payment verified successfully. Inspection can now begin."
}
```

**Frontend Implementation:**
```javascript
async function verifyPayment(inspectionId, reference) {
  try {
    const response = await fetch(`/api/v1/inspections/${inspectionId}/verify-payment/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        reference: reference
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('Payment verified! Inspection can now begin.');
      window.location.href = `/inspections/${inspectionId}`;
    } else {
      alert('Payment verification failed: ' + data.error);
    }
  } catch (error) {
    console.error('Verification error:', error);
  }
}
```

---


### STEP 4: Conduct Inspection (Inspector Only)

**Purpose:** Inspector collects inspection data and uploads photos.

#### 4a. Get Inspection Details

**Endpoint:** `GET /api/v1/inspections/{inspection_id}/`

**Response:**
```json
{
  "id": 1,
  "vehicle": {
    "id": 123,
    "name": "Toyota Camry 2020",
    "brand": "Toyota",
    "model": "Camry",
    "color": "Silver",
    "condition": "Used",
    "mileage": 45000
  },
  "inspector": {
    "id": 456,
    "name": "John Mechanic",
    "email": "john@example.com"
  },
  "customer": {
    "id": 789,
    "name": "Jane Customer",
    "email": "jane@example.com"
  },
  "dealer": {
    "id": 101,
    "name": "AutoHub Motors",
    "email": "info@autohub.com"
  },
  "inspection_type": "pre_purchase",
  "status": "draft",
  "payment_status": "paid",
  "inspection_fee": 50000.00,
  "paid_at": "2024-01-15T10:30:00Z",
  "exterior_data": {},
  "interior_data": {},
  "engine_data": {},
  "mechanical_data": {},
  "safety_data": {},
  "documentation_data": {},
  "inspector_notes": "",
  "recommended_actions": [],
  "photos": [],
  "documents": []
}
```

#### 4b. Update Inspection Data

**Endpoint:** `PUT /api/v1/inspections/{inspection_id}/`

**Request:**
```json
{
  "status": "in_progress",
  "exterior_data": {
    "body_condition": "good",
    "paint_condition": "excellent",
    "windshield_condition": "good",
    "lights_condition": "excellent",
    "mirrors_condition": "good"
  },
  "interior_data": {
    "seats_condition": "good",
    "dashboard_condition": "excellent",
    "steering_condition": "good",
    "ac_condition": "excellent"
  },
  "engine_data": {
    "engine_condition": "good",
    "oil_level": "excellent",
    "coolant_level": "good",
    "battery_condition": "good"
  },
  "mechanical_data": {
    "transmission_condition": "good",
    "brakes_condition": "fair",
    "suspension_condition": "good",
    "exhaust_condition": "good"
  },
  "safety_data": {
    "airbags_condition": "excellent",
    "seatbelts_condition": "good",
    "abs_condition": "good"
  },
  "inspector_notes": "Vehicle is in good overall condition. Brake pads need replacement soon.",
  "recommended_actions": [
    "Replace brake pads within 1 month",
    "Check tire pressure regularly",
    "Service air conditioning system"
  ]
}
```

**Frontend Implementation:**
```javascript
async function updateInspectionData(inspectionId, inspectionData) {
  const response = await fetch(`/api/v1/inspections/${inspectionId}/`, {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(inspectionData)
  });
  
  return await response.json();
}
```

#### 4c. Upload Photos

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/photos/`

**Request (FormData):**
```javascript
const formData = new FormData();
formData.append('category', 'exterior_front');
formData.append('image', fileInput.files[0]);
formData.append('description', 'Front view of vehicle');
```

**Response:**
```json
{
  "id": 1,
  "category": "exterior_front",
  "image": "https://res.cloudinary.com/veyu/image/upload/v1234567890/inspections/photos/abc123.jpg",
  "description": "Front view of vehicle",
  "date_created": "2024-01-15T11:00:00Z"
}
```

**Frontend Implementation:**
```javascript
async function uploadInspectionPhoto(inspectionId, category, file, description = '') {
  const formData = new FormData();
  formData.append('category', category);
  formData.append('image', file);
  formData.append('description', description);
  
  const response = await fetch(`/api/v1/inspections/${inspectionId}/photos/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`
    },
    body: formData
  });
  
  return await response.json();
}
```

**Photo Categories:**
- `exterior_front` - Exterior - Front View
- `exterior_rear` - Exterior - Rear View
- `exterior_left` - Exterior - Left Side
- `exterior_right` - Exterior - Right Side
- `interior_dashboard` - Interior - Dashboard
- `interior_seats` - Interior - Seats
- `engine_bay` - Engine Bay
- `tires_wheels` - Tires and Wheels
- `damage_detail` - Damage Detail
- `documents` - Vehicle Documents
- `other` - Other

---


### STEP 5: Complete Inspection

**Purpose:** Inspector marks the inspection as complete.

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/complete/`

**Response:**
```json
{
  "success": true,
  "message": "Inspection marked as completed",
  "data": {
    "inspection_id": 1,
    "status": "Completed",
    "completed_at": "2024-01-15T12:00:00Z"
  }
}
```

**Frontend Implementation:**
```javascript
async function completeInspection(inspectionId) {
  const response = await fetch(`/api/v1/inspections/${inspectionId}/complete/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    }
  });
  
  const data = await response.json();
  
  if (data.success) {
    alert('Inspection completed successfully!');
    // Redirect to document generation
  }
  
  return data;
}
```

---

### STEP 6: Generate Document

**Purpose:** Generate PDF inspection report.

**Endpoint:** `POST /api/v1/inspections/{inspection_id}/generate-document/`

**Request:**
```json
{
  "template_type": "standard",
  "include_photos": true,
  "include_recommendations": true,
  "language": "en",
  "compliance_standards": ["NURTW", "FRSC"]
}
```

**Template Types:**
- `standard` - Standard Report
- `detailed` - Detailed Report
- `legal` - Legal Compliance Report

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "template_type": "standard",
    "status": "ready",
    "document_file": "https://res.cloudinary.com/veyu/raw/upload/v1234567890/inspections/documents/inspection_1.pdf",
    "page_count": 5,
    "file_size": 2048576,
    "formatted_file_size": "2.0 MB",
    "generated_at": "2024-01-15T12:05:00Z",
    "expires_at": "2024-01-16T12:05:00Z",
    "signatures": [
      {
        "id": 1,
        "role": "inspector",
        "role_display": "Inspector",
        "status": "pending",
        "signer_name": "John Mechanic"
      },
      {
        "id": 2,
        "role": "customer",
        "role_display": "Customer",
        "status": "pending",
        "signer_name": "Jane Customer"
      },
      {
        "id": 3,
        "role": "dealer",
        "role_display": "Dealer Representative",
        "status": "pending",
        "signer_name": "AutoHub Motors"
      }
    ]
  },
  "message": "Document generated successfully"
}
```

**Frontend Implementation:**
```javascript
async function generateDocument(inspectionId, options = {}) {
  const defaultOptions = {
    template_type: 'standard',
    include_photos: true,
    include_recommendations: true,
    language: 'en',
    compliance_standards: []
  };
  
  const response = await fetch(`/api/v1/inspections/${inspectionId}/generate-document/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ ...defaultOptions, ...options })
  });
  
  return await response.json();
}
```

---


### STEP 7: Sign Document (All Parties)

**Purpose:** Inspector, Customer, and Dealer sign the inspection document.

#### 7a. Preview Document

**Endpoint:** `GET /api/v1/inspections/documents/{document_id}/preview/`

**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": 1,
    "preview_url": "https://res.cloudinary.com/veyu/raw/upload/v1234567890/inspections/documents/inspection_1.pdf",
    "thumbnail_url": null,
    "page_count": 5,
    "document_size": "2.0 MB",
    "metadata": {
      "title": "Vehicle Inspection Report - Toyota Camry 2020",
      "created_at": "2024-01-15T12:05:00Z",
      "inspector": "John Mechanic",
      "vehicle_vin": "1HGBH41JXMN109186"
    },
    "signature_fields": [
      {
        "field_id": "inspector_signature",
        "role": "inspector",
        "page": 5,
        "coordinates": {
          "x": 100,
          "y": 200,
          "width": 200,
          "height": 50
        },
        "required": true,
        "status": "pending"
      },
      {
        "field_id": "customer_signature",
        "role": "customer",
        "page": 5,
        "coordinates": {
          "x": 350,
          "y": 200,
          "width": 200,
          "height": 50
        },
        "required": true,
        "status": "pending"
      },
      {
        "field_id": "dealer_signature",
        "role": "dealer",
        "page": 5,
        "coordinates": {
          "x": 600,
          "y": 200,
          "width": 200,
          "height": 50
        },
        "required": true,
        "status": "pending"
      }
    ],
    "status": {
      "document_id": 1,
      "status": "Ready for Signature",
      "generated_at": "2024-01-15T12:05:00Z",
      "expires_at": "2024-01-16T12:05:00Z",
      "is_expired": false,
      "total_signatures": 3,
      "completed_signatures": 0,
      "pending_signatures": 3
    }
  }
}
```

#### 7b. Submit Signature

**Endpoint:** `POST /api/v1/inspections/documents/{document_id}/sign/`

**Request:**
```json
{
  "signature_data": {
    "signature_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "signature_method": "drawn",
    "coordinates": {
      "x": 100,
      "y": 200,
      "width": 200,
      "height": 50
    }
  },
  "signature_field_id": "inspector_signature",
  "signature_method": "drawn"
}
```

**Signature Methods:**
- `drawn` - Hand drawn signature
- `typed` - Typed name
- `uploaded` - Uploaded image

**Response:**
```json
{
  "success": true,
  "data": {
    "signature_id": 1,
    "status": "Signed",
    "signed_at": "2024-01-15T12:10:00Z",
    "document_status": "Ready for Signature"
  },
  "message": "Signature submitted successfully"
}
```

**Frontend Implementation (Canvas Signature):**
```javascript
// HTML Canvas for signature
// <canvas id="signatureCanvas" width="400" height="200"></canvas>

async function submitSignature(documentId, signatureFieldId) {
  const canvas = document.getElementById('signatureCanvas');
  const signatureImage = canvas.toDataURL('image/png');
  
  const response = await fetch(`/api/v1/inspections/documents/${documentId}/sign/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      signature_data: {
        signature_image: signatureImage,
        signature_method: 'drawn',
        coordinates: {
          x: 100,
          y: 200,
          width: 200,
          height: 50
        }
      },
      signature_field_id: signatureFieldId,
      signature_method: 'drawn'
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    alert('Signature submitted successfully!');
    // Check if all signatures are complete
    checkDocumentStatus(documentId);
  }
  
  return data;
}
```

**Signature Pad Library (Recommended):**
```html
<!-- Include signature_pad library -->
<script src="https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js"></script>

<canvas id="signatureCanvas"></canvas>
<button onclick="clearSignature()">Clear</button>
<button onclick="saveSignature()">Sign Document</button>

<script>
const canvas = document.getElementById('signatureCanvas');
const signaturePad = new SignaturePad(canvas);

function clearSignature() {
  signaturePad.clear();
}

async function saveSignature() {
  if (signaturePad.isEmpty()) {
    alert('Please provide a signature');
    return;
  }
  
  const signatureImage = signaturePad.toDataURL('image/png');
  await submitSignature(documentId, signatureFieldId);
}
</script>
```

---


### STEP 8: Download Signed Document

**Purpose:** Download the fully signed inspection document.

**Endpoint:** `GET /api/v1/inspections/documents/{document_id}/download/`

**Response:** PDF file download

**Frontend Implementation:**
```javascript
async function downloadDocument(documentId) {
  const response = await fetch(`/api/v1/inspections/documents/${documentId}/download/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${authToken}`
    }
  });
  
  if (response.ok) {
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `inspection_${documentId}.pdf`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } else {
    alert('Failed to download document');
  }
}
```

---

## Data Models

### Inspection Status Flow

```
pending_payment → draft → in_progress → completed → signed → archived
```

**Status Descriptions:**
- `pending_payment` - Awaiting payment
- `draft` - Payment completed, ready to start
- `in_progress` - Inspector is conducting inspection
- `completed` - Inspection finished, awaiting signatures
- `signed` - All parties have signed
- `archived` - Inspection archived

### Payment Status

```
unpaid → paid
  ↓
refunded / failed
```

**Payment Status Descriptions:**
- `unpaid` - Payment not yet made
- `paid` - Payment successful
- `refunded` - Payment refunded to customer
- `failed` - Payment attempt failed

### Inspection Types

| Type | Code | Fee |
|------|------|-----|
| Pre-Purchase Inspection | `pre_purchase` | ₦50,000 |
| Pre-Rental Inspection | `pre_rental` | ₦30,000 |
| Maintenance Inspection | `maintenance` | ₦25,000 |
| Insurance Inspection | `insurance` | ₦40,000 |

### Condition Ratings

- `excellent` - Excellent condition
- `good` - Good condition
- `fair` - Fair condition (may need attention)
- `poor` - Poor condition (needs immediate attention)

---

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "error": "Inspection has already been paid for"
}
```

#### 403 Forbidden
```json
{
  "error": "Only the customer can pay for this inspection"
}
```

#### 404 Not Found
```json
{
  "error": "Inspection not found"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Failed to process payment"
}
```

### Error Handling Implementation

```javascript
async function handleApiCall(apiFunction) {
  try {
    const response = await apiFunction();
    
    if (response.error) {
      // Handle error
      showError(response.error);
      return null;
    }
    
    return response;
  } catch (error) {
    console.error('API Error:', error);
    showError('An unexpected error occurred. Please try again.');
    return null;
  }
}

function showError(message) {
  // Display error to user
  alert(message);
  // Or use a toast notification library
}
```

---


## UI/UX Recommendations

### 1. Payment Page

```
┌─────────────────────────────────────────────────────┐
│  Pay for Inspection                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Inspection Details:                                │
│  • Type: Pre-Purchase Inspection                    │
│  • Vehicle: Toyota Camry 2020                       │
│  • Inspector: John Mechanic                         │
│                                                     │
│  Amount to Pay: ₦50,000.00                          │
│                                                     │
│  Payment Method:                                    │
│  ○ Wallet (Balance: ₦500,000)                       │
│  ○ Bank (Card, Transfer, USSD)                      │
│                                                     │
│  [Pay Now]                                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2. Inspection Form (Inspector)

```
┌─────────────────────────────────────────────────────┐
│  Vehicle Inspection                                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Exterior] [Interior] [Engine] [Mechanical] [Safety]│
│                                                     │
│  Exterior Inspection:                               │
│  • Body Condition:     [Excellent ▼]                │
│  • Paint Condition:    [Good ▼]                     │
│  • Windshield:         [Good ▼]                     │
│  • Lights:             [Excellent ▼]                │
│                                                     │
│  Photos:                                            │
│  [📷 Upload Front View]                             │
│  [📷 Upload Rear View]                              │
│  [📷 Upload Left Side]                              │
│  [📷 Upload Right Side]                             │
│                                                     │
│  Inspector Notes:                                   │
│  [Text area for notes...]                           │
│                                                     │
│  Recommended Actions:                               │
│  • [+ Add recommendation]                           │
│                                                     │
│  [Save Draft] [Complete Inspection]                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 3. Document Signing Page

```
┌─────────────────────────────────────────────────────┐
│  Sign Inspection Document                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Document Preview:                                  │
│  ┌───────────────────────────────────────────┐     │
│  │                                           │     │
│  │     [PDF Preview]                         │     │
│  │                                           │     │
│  └───────────────────────────────────────────┘     │
│                                                     │
│  Signature Required:                                │
│  Role: Inspector                                    │
│                                                     │
│  Draw your signature below:                         │
│  ┌───────────────────────────────────────────┐     │
│  │                                           │     │
│  │     [Signature Canvas]                    │     │
│  │                                           │     │
│  └───────────────────────────────────────────┘     │
│                                                     │
│  [Clear] [Sign Document]                            │
│                                                     │
│  Signatures Status:                                 │
│  ✓ Inspector: Signed                                │
│  ○ Customer: Pending                                │
│  ○ Dealer: Pending                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 4. Inspection Dashboard

```
┌─────────────────────────────────────────────────────┐
│  My Inspections                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [+ New Inspection]                                 │
│                                                     │
│  Filters: [All ▼] [Type ▼] [Status ▼]              │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Toyota Camry 2020                           │   │
│  │ Pre-Purchase Inspection                     │   │
│  │ Status: Pending Payment                     │   │
│  │ Fee: ₦50,000                                │   │
│  │ [Pay Now]                                   │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Honda Accord 2019                           │   │
│  │ Pre-Rental Inspection                       │   │
│  │ Status: In Progress                         │   │
│  │ Inspector: John Mechanic                    │   │
│  │ [View Details]                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Mercedes Benz C300 2021                     │   │
│  │ Pre-Purchase Inspection                     │   │
│  │ Status: Completed                           │   │
│  │ Awaiting Signatures: 2/3                    │   │
│  │ [Sign Document]                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 5. Status Indicators

Use color coding for status:

- 🔴 **Pending Payment** - Red
- 🟡 **Draft** - Yellow
- 🔵 **In Progress** - Blue
- 🟢 **Completed** - Green
- ✅ **Signed** - Green with checkmark
- ⚫ **Archived** - Gray

### 6. Loading States

Show loading indicators during:
- Payment processing
- Document generation
- Photo uploads
- Signature submission

```javascript
// Example loading state
<button disabled={isLoading}>
  {isLoading ? 'Processing...' : 'Pay Now'}
</button>
```

### 7. Notifications

Notify users when:
- Payment is successful
- Inspection is assigned to them
- Inspection is completed
- Document is ready for signing
- All signatures are collected
- Document is available for download

---

## Complete Example Flow (React)

```jsx
import React, { useState, useEffect } from 'react';
import { PaystackButton } from 'react-paystack';

function InspectionFlow() {
  const [step, setStep] = useState(1);
  const [inspection, setInspection] = useState(null);
  const [quote, setQuote] = useState(null);
  
  // Step 1: Get Quote
  const getQuote = async () => {
    const response = await fetch('/api/v1/inspections/quote/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inspection_type: 'pre_purchase',
        vehicle_id: vehicleId
      })
    });
    const data = await response.json();
    setQuote(data.data);
    setStep(2);
  };
  
  // Step 2: Create Inspection
  const createInspection = async () => {
    const response = await fetch('/api/v1/inspections/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        vehicle: vehicleId,
        inspector: inspectorId,
        customer: customerId,
        dealer: dealerId,
        inspection_type: 'pre_purchase'
      })
    });
    const data = await response.json();
    setInspection(data);
    setStep(3);
  };
  
  // Step 3: Pay with Wallet
  const payWithWallet = async () => {
    const response = await fetch(`/api/v1/inspections/${inspection.id}/pay/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        payment_method: 'wallet',
        amount: inspection.inspection_fee
      })
    });
    const data = await response.json();
    if (data.success) {
      alert('Payment successful!');
      setStep(4);
    }
  };
  
  return (
    <div>
      {step === 1 && (
        <div>
          <h2>Get Fee Quote</h2>
          <button onClick={getQuote}>Get Quote</button>
        </div>
      )}
      
      {step === 2 && quote && (
        <div>
          <h2>Fee Quote</h2>
          <p>Type: {quote.inspection_type}</p>
          <p>Fee: ₦{quote.total_fee.toLocaleString()}</p>
          <button onClick={createInspection}>Book Inspection</button>
        </div>
      )}
      
      {step === 3 && inspection && (
        <div>
          <h2>Pay for Inspection</h2>
          <p>Amount: ₦{inspection.inspection_fee.toLocaleString()}</p>
          <button onClick={payWithWallet}>Pay with Wallet</button>
        </div>
      )}
      
      {step === 4 && (
        <div>
          <h2>Inspection Booked!</h2>
          <p>Your inspection has been scheduled.</p>
          <p>Status: {inspection.status_display}</p>
        </div>
      )}
    </div>
  );
}
```

---

## Testing

### Test Credentials

**Paystack Test Cards:**

| Card Number | CVV | Expiry | PIN | OTP | Result |
|-------------|-----|--------|-----|-----|--------|
| 4084084084084081 | 408 | 12/30 | 0000 | 123456 | Success |
| 5060666666666666666 | 123 | 12/30 | 1234 | 123456 | Success |
| 4084084084084081 | 408 | 12/30 | 0000 | 000000 | Failed |

### Test Scenarios

1. **Wallet Payment Success**
   - Create inspection
   - Ensure wallet has sufficient balance
   - Pay with wallet
   - Verify status changes to 'draft'

2. **Wallet Payment Insufficient Balance**
   - Create inspection
   - Ensure wallet has insufficient balance
   - Attempt payment
   - Verify error message shown

3. **Bank Payment Success**
   - Create inspection
   - Initiate bank payment
   - Complete Paystack checkout
   - Verify payment
   - Verify status changes to 'draft'

4. **Complete Inspection Flow**
   - Create and pay for inspection
   - Conduct inspection (add data and photos)
   - Complete inspection
   - Generate document
   - Sign document (all parties)
   - Download signed document

---

## Support

For implementation questions or issues:
- Backend API: Check `inspections/README.md`
- Payment Integration: Check `inspections/PAYSTACK_INTEGRATION.md`
- Complete Flow: Check `inspections/COMPLETE_FLOW.md`

**API Base URL:**
- Production: `https://veyu.cc/api/v1`
- Staging: `https://staging.veyu.cc/api/v1`

**Paystack Public Keys:**
- Test: `pk_test_xxxxxxxxxxxxx`
- Live: `pk_live_xxxxxxxxxxxxx`

---

**Last Updated:** November 26, 2024  
**Version:** 1.0.0
