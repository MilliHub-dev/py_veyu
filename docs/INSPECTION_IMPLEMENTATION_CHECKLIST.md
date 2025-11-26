# Inspection System - Frontend Implementation Checklist

## 📋 Overview

This checklist helps frontend developers implement the complete inspection flow from payment to document signing.

---

## 🎯 Implementation Steps

### Phase 1: Payment Integration

- [ ] **Step 1.1:** Create fee quote page
  - [ ] Add form to select inspection type
  - [ ] Call `POST /inspections/quote/` API
  - [ ] Display fee amount to user
  
- [ ] **Step 1.2:** Create inspection booking page
  - [ ] Add form with vehicle, inspector, dealer selection
  - [ ] Call `POST /inspections/` API
  - [ ] Handle response with inspection ID

- [ ] **Step 1.3:** Implement wallet payment
  - [ ] Add "Pay with Wallet" button
  - [ ] Call `POST /inspections/{id}/pay/` with `payment_method: "wallet"`
  - [ ] Handle success/error responses
  - [ ] Show remaining balance after payment

- [ ] **Step 1.4:** Implement Paystack integration
  - [ ] Include Paystack script: `https://js.paystack.co/v1/inline.js`
  - [ ] Add "Pay with Bank" button
  - [ ] Call `POST /inspections/{id}/pay/` with `payment_method: "bank"`
  - [ ] Open Paystack popup with returned reference
  - [ ] Handle payment success callback
  - [ ] Call `POST /inspections/{id}/verify-payment/` to verify
  - [ ] Redirect to inspection page after verification

---

### Phase 2: Inspection Data Collection (Inspector View)

- [ ] **Step 2.1:** Create inspection detail page
  - [ ] Call `GET /inspections/{id}/` to load inspection
  - [ ] Display vehicle details
  - [ ] Show payment status
  - [ ] Only allow access if payment is complete

- [ ] **Step 2.2:** Create inspection form
  - [ ] Add tabs for: Exterior, Interior, Engine, Mechanical, Safety
  - [ ] Add dropdown selects for condition ratings (excellent/good/fair/poor)
  - [ ] Add text area for inspector notes
  - [ ] Add dynamic list for recommended actions
  - [ ] Call `PUT /inspections/{id}/` to save data

- [ ] **Step 2.3:** Implement photo upload
  - [ ] Add file input for each photo category
  - [ ] Show preview before upload
  - [ ] Call `POST /inspections/{id}/photos/` for each photo
  - [ ] Display uploaded photos with thumbnails
  - [ ] Allow photo deletion

- [ ] **Step 2.4:** Add complete button
  - [ ] Add "Complete Inspection" button
  - [ ] Validate all required fields are filled
  - [ ] Call `POST /inspections/{id}/complete/`
  - [ ] Show success message
  - [ ] Redirect to document generation

---

### Phase 3: Document Generation

- [ ] **Step 3.1:** Create document generation page
  - [ ] Add template type selector (standard/detailed/legal)
  - [ ] Add checkboxes for include_photos and include_recommendations
  - [ ] Call `POST /inspections/{id}/generate-document/`
  - [ ] Show loading indicator during generation
  - [ ] Display success message with document ID

- [ ] **Step 3.2:** Handle document generation errors
  - [ ] Show error if inspection not completed
  - [ ] Show error if document already exists
  - [ ] Provide retry option

---

### Phase 4: Document Signing

- [ ] **Step 4.1:** Create document preview page
  - [ ] Call `GET /inspections/documents/{doc_id}/preview/`
  - [ ] Embed PDF preview (use iframe or PDF.js)
  - [ ] Display signature status for all parties
  - [ ] Show which signatures are pending

- [ ] **Step 4.2:** Implement signature pad
  - [ ] Include signature_pad library
  - [ ] Create canvas element for drawing
  - [ ] Add "Clear" button
  - [ ] Add "Sign" button
  - [ ] Convert canvas to base64 image

- [ ] **Step 4.3:** Submit signature
  - [ ] Call `POST /inspections/documents/{doc_id}/sign/`
  - [ ] Send signature image as base64
  - [ ] Handle success response
  - [ ] Update signature status in UI
  - [ ] Check if all signatures are complete

- [ ] **Step 4.4:** Handle signature completion
  - [ ] Show notification when all signatures collected
  - [ ] Enable download button
  - [ ] Update document status to "signed"

---

### Phase 5: Document Download

- [ ] **Step 5.1:** Implement download functionality
  - [ ] Add "Download PDF" button
  - [ ] Call `GET /inspections/documents/{doc_id}/download/`
  - [ ] Handle blob response
  - [ ] Trigger file download
  - [ ] Show success message

---

### Phase 6: Dashboard & Listing

- [ ] **Step 6.1:** Create inspections list page
  - [ ] Call `GET /inspections/` to list all inspections
  - [ ] Display inspection cards with key info
  - [ ] Add filters: status, type, date range
  - [ ] Add search functionality
  - [ ] Show payment status badges
  - [ ] Add action buttons based on status

- [ ] **Step 6.2:** Add status indicators
  - [ ] Use color coding for statuses
  - [ ] Show progress indicators
  - [ ] Display next action required

---

## 🎨 UI Components Needed

### Components to Build

- [ ] `InspectionQuoteForm` - Get fee quote
- [ ] `InspectionBookingForm` - Create inspection
- [ ] `PaymentMethodSelector` - Choose wallet or bank
- [ ] `PaystackCheckout` - Paystack integration
- [ ] `InspectionForm` - Data collection form
- [ ] `PhotoUploader` - Upload inspection photos
- [ ] `DocumentGenerator` - Generate PDF
- [ ] `SignaturePad` - Draw signature
- [ ] `DocumentPreview` - Preview PDF
- [ ] `InspectionCard` - List item
- [ ] `InspectionDashboard` - Main dashboard
- [ ] `StatusBadge` - Status indicator

---

## 🔧 Utilities to Create

- [ ] `api.js` - API client with all endpoints
- [ ] `auth.js` - Authentication helpers
- [ ] `paystack.js` - Paystack integration helpers
- [ ] `validation.js` - Form validation
- [ ] `formatters.js` - Currency, date formatters
- [ ] `constants.js` - Inspection types, statuses, etc.

---

## 📱 Responsive Design

- [ ] Mobile-friendly forms
- [ ] Touch-friendly signature pad
- [ ] Responsive photo upload
- [ ] Mobile PDF preview
- [ ] Responsive dashboard

---

## ✅ Testing Checklist

### Wallet Payment
- [ ] Test with sufficient balance
- [ ] Test with insufficient balance
- [ ] Test duplicate payment prevention
- [ ] Test unauthorized access

### Bank Payment
- [ ] Test Paystack popup opens
- [ ] Test successful payment
- [ ] Test payment cancellation
- [ ] Test payment verification
- [ ] Test with test cards

### Inspection Flow
- [ ] Test data collection
- [ ] Test photo upload
- [ ] Test form validation
- [ ] Test completion
- [ ] Test unauthorized access

### Document Flow
- [ ] Test document generation
- [ ] Test PDF preview
- [ ] Test signature submission
- [ ] Test multiple signatures
- [ ] Test document download

---

## 🚀 Deployment

- [ ] Set environment variables
  - [ ] `REACT_APP_API_URL`
  - [ ] `REACT_APP_PAYSTACK_PUBLIC_KEY`
- [ ] Test on staging
- [ ] Test with real Paystack test cards
- [ ] Verify all API endpoints work
- [ ] Test error handling
- [ ] Deploy to production

---

## 📚 Documentation References

- **Complete Guide:** `docs/INSPECTION_FRONTEND_GUIDE.md`
- **API Reference:** `docs/INSPECTION_API_QUICK_REFERENCE.md`
- **Paystack Integration:** `inspections/PAYSTACK_INTEGRATION.md`
- **Flow Diagram:** `inspections/COMPLETE_FLOW.md`

---

## 🆘 Support

**Questions?**
- Check documentation first
- Review API responses
- Test with Postman/curl
- Contact backend team

**Common Issues:**
- CORS errors → Check API URL
- Auth errors → Verify JWT token
- Payment errors → Check Paystack keys
- Upload errors → Check file size/format

---

**Last Updated:** November 26, 2024  
**Version:** 1.0.0
