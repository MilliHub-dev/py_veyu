# Vehicle Inspection System

## Overview

The Vehicle Inspection System is a comprehensive solution for managing vehicle inspections, generating inspection reports, collecting digital signatures, and managing inspection documents with full audit trails and access controls.

## Design

The inspection slip PDFs feature a professional, modern design with:
- **Veyu Logo**: Branded header with company logo
- **Color-Coded Ratings**: Visual indicators for inspection results
- **Professional Layout**: Clean, organized information presentation
- **Icons**: Visual elements for better readability
- **Signature Boxes**: Styled signature sections for all parties

See [DESIGN_GUIDE.md](./DESIGN_GUIDE.md) for detailed design specifications.

### Creating the Logo

Before generating inspection reports, create the Veyu logo:

```bash
python manage.py create_inspection_logo
```

This creates the logo at `static/images/veyu-logo.png`

## Features

### 1. Vehicle Inspection Management
- Create and manage vehicle inspections
- Support for multiple inspection types (pre-purchase, pre-rental, maintenance, insurance)
- Comprehensive inspection data collection (exterior, interior, engine, mechanical, safety)
- Photo upload and management
- Inspector notes and recommendations
- Overall rating calculation

### 2. PDF Document Generation
- Generate professional inspection reports in PDF format
- Multiple template types (standard, detailed, legal compliance)
- Customizable report content (photos, recommendations)
- Multi-language support
- Legal compliance features

### 3. Digital Signature Integration
- Multi-party signature support (inspector, customer, dealer)
- Signature validation and verification
- Tamper-proof signature storage
- Comprehensive audit trail
- Signature status tracking
- Rate limiting and security features

### 4. Frontend Integration APIs
- Simplified endpoints for frontend applications
- Inspection data collection
- Document preview generation
- Signature submission
- Real-time status updates
- Form schema for dynamic form generation

### 5. Document Management System
- Secure document storage with access controls
- Document versioning and history
- Comprehensive audit trail
- Advanced search and filtering
- Document retention and archival policies
- Document sharing and permission management

## API Endpoints

### Inspection Endpoints

#### List/Create Inspections
```
GET/POST /api/v1/inspections/
```

#### Get/Update/Delete Inspection
```
GET/PUT/DELETE /api/v1/inspections/{id}/
```

#### Complete Inspection
```
POST /api/v1/inspections/{id}/complete/
```

#### Upload Photos
```
POST /api/v1/inspections/{id}/photos/
```

### Document Endpoints

#### Generate Document
```
POST /api/v1/inspections/{inspection_id}/generate-document/
```

#### Document Preview
```
GET /api/v1/inspections/documents/{document_id}/preview/
```

#### Download Document
```
GET /api/v1/inspections/documents/{document_id}/download/
```

#### Sign Document
```
POST /api/v1/inspections/documents/{document_id}/sign/
```

### Signature Endpoints

#### Validate Signature
```
POST /api/v1/inspections/signatures/validate/
```

#### Check Signature Permission
```
GET /api/v1/inspections/signatures/documents/{document_id}/permission-check/
```

#### Get Signature Status
```
GET /api/v1/inspections/signatures/documents/{document_id}/status/
```

#### Get Audit Trail
```
GET /api/v1/inspections/signatures/documents/{document_id}/audit-trail/
```

#### Verify Signature
```
POST /api/v1/inspections/signatures/{signature_id}/verify/
```

#### Resend Notification
```
POST /api/v1/inspections/signatures/{signature_id}/resend-notification/
```

#### Reject Signature
```
POST /api/v1/inspections/signatures/{signature_id}/reject/
```

### Frontend Integration Endpoints

#### Collect Inspection Data
```
POST /api/v1/inspections/frontend/collect-data/
```

#### Generate Document Preview
```
POST /api/v1/inspections/frontend/inspections/{inspection_id}/generate-preview/
```

#### Submit Signature
```
POST /api/v1/inspections/frontend/documents/{document_id}/submit-signature/
```

#### Retrieve Document
```
GET /api/v1/inspections/frontend/documents/{document_id}/
```

#### Get Inspection Status
```
GET /api/v1/inspections/frontend/inspections/{inspection_id}/status/
```

#### Upload Photo
```
POST /api/v1/inspections/frontend/inspections/{inspection_id}/upload-photo/
```

#### Get Form Schema
```
GET /api/v1/inspections/frontend/form-schema/
```

### Document Management Endpoints

#### Check Access
```
GET /api/v1/inspections/management/documents/{document_id}/access-check/
```

#### Get Version History
```
GET /api/v1/inspections/management/documents/{document_id}/versions/
```

#### Get Audit Trail
```
GET /api/v1/inspections/management/documents/{document_id}/audit-trail/
```

#### Search Documents
```
POST /api/v1/inspections/management/documents/search/
```

#### Check Retention Status
```
GET /api/v1/inspections/management/documents/{document_id}/retention-status/
```

#### Archive Document
```
POST /api/v1/inspections/management/documents/{document_id}/archive/
```

#### Share Document
```
POST /api/v1/inspections/management/documents/{document_id}/share/
```

#### List Shares
```
GET /api/v1/inspections/management/documents/{document_id}/shares/
```

#### Revoke Share
```
POST /api/v1/inspections/management/documents/{document_id}/revoke-share/
```

#### Run Retention Cleanup (Admin Only)
```
POST /api/v1/inspections/management/documents/retention-cleanup/
```

## Models

### VehicleInspection
Main model for vehicle inspection records.

**Fields:**
- `vehicle` - Foreign key to Vehicle
- `inspector` - Foreign key to Account (inspector)
- `customer` - Foreign key to Customer
- `dealer` - Foreign key to Dealership
- `inspection_type` - Type of inspection
- `status` - Current status
- `overall_rating` - Overall condition rating
- `exterior_data` - JSON field for exterior inspection data
- `interior_data` - JSON field for interior inspection data
- `engine_data` - JSON field for engine inspection data
- `mechanical_data` - JSON field for mechanical inspection data
- `safety_data` - JSON field for safety inspection data
- `documentation_data` - JSON field for documentation data
- `inspector_notes` - Text field for notes
- `recommended_actions` - JSON field for recommendations
- `inspection_date` - Date of inspection
- `completed_at` - Completion timestamp

### InspectionPhoto
Model for storing inspection photos.

**Fields:**
- `inspection` - Foreign key to VehicleInspection
- `category` - Photo category
- `image` - Cloudinary image field
- `description` - Photo description

### InspectionDocument
Model for generated inspection documents.

**Fields:**
- `inspection` - Foreign key to VehicleInspection
- `template_type` - Template type used
- `status` - Document status
- `document_file` - Cloudinary file field
- `document_hash` - SHA-256 hash for integrity
- `file_size` - File size in bytes
- `page_count` - Number of pages
- `include_photos` - Whether photos are included
- `include_recommendations` - Whether recommendations are included
- `language` - Document language
- `compliance_standards` - JSON field for compliance standards
- `generated_at` - Generation timestamp
- `expires_at` - Expiration timestamp

### DigitalSignature
Model for storing digital signatures.

**Fields:**
- `document` - Foreign key to InspectionDocument
- `signer` - Foreign key to Account
- `role` - Signer role (inspector, customer, dealer)
- `status` - Signature status
- `signature_image` - Cloudinary image field
- `signature_method` - Method used (drawn, typed, uploaded)
- `signed_at` - Signature timestamp
- `signer_ip` - IP address of signer
- `signer_user_agent` - User agent string
- `signature_coordinates` - JSON field for coordinates
- `signature_hash` - SHA-256 hash for verification
- `is_verified` - Verification status

### InspectionTemplate
Model for storing inspection report templates.

**Fields:**
- `name` - Template name
- `category` - Template category
- `description` - Template description
- `template_file` - Template file
- `is_active` - Active status
- `supports_photos` - Whether template supports photos
- `supports_recommendations` - Whether template supports recommendations
- `compliance_standards` - JSON field for compliance standards
- `created_by` - Foreign key to Account
- `version` - Template version

## Services

### PDFGenerationService
Handles PDF generation for inspection reports using ReportLab.

**Methods:**
- `generate_inspection_pdf()` - Generate PDF document
- `_build_standard_content()` - Build standard report content
- `_build_detailed_content()` - Build detailed report content
- `_build_legal_content()` - Build legal compliance report content

### DocumentManagementService
Manages inspection documents and signatures.

**Methods:**
- `create_inspection_document()` - Create new document
- `submit_signature()` - Submit digital signature
- `get_document_status()` - Get document status

### InspectionValidationService
Validates inspection data and business logic.

**Methods:**
- `validate_inspection_data()` - Validate inspection data structure
- `calculate_overall_rating()` - Calculate overall rating

### DocumentAccessControl
Manages access control for documents.

**Methods:**
- `check_access()` - Check user access level
- `can_view()` - Check view permission
- `can_download()` - Check download permission
- `can_sign()` - Check sign permission
- `can_manage()` - Check manage permission

### DocumentVersionManager
Manages document versioning.

**Methods:**
- `create_version()` - Create new version
- `get_version_history()` - Get version history

### DocumentAuditTrail
Manages audit trail for documents.

**Methods:**
- `log_access()` - Log access event
- `log_modification()` - Log modification event
- `get_audit_trail()` - Get audit trail

### DocumentSearchManager
Manages document search and filtering.

**Methods:**
- `search_documents()` - Search documents with filters

### DocumentRetentionManager
Manages document retention and archival.

**Methods:**
- `check_retention_policy()` - Check retention status
- `archive_document()` - Archive document
- `delete_expired_documents()` - Delete expired documents
- `archive_old_documents()` - Archive old documents

### DocumentSharingManager
Manages document sharing.

**Methods:**
- `share_document()` - Share document with user
- `revoke_share()` - Revoke document share
- `get_document_shares()` - Get document shares

### SignatureValidator
Validates digital signatures.

**Methods:**
- `validate_signature_image()` - Validate signature image
- `generate_signature_hash()` - Generate signature hash
- `verify_signature_integrity()` - Verify signature integrity

### SignatureAuditLogger
Logs signature-related events.

**Methods:**
- `log_signature_attempt()` - Log signature attempt
- `log_signature_verification()` - Log verification
- `log_document_access()` - Log document access

### SignatureSecurityManager
Manages signature security policies.

**Methods:**
- `check_signature_permissions()` - Check permissions
- `validate_signature_timing()` - Validate timing
- `check_signature_rate_limit()` - Check rate limit

### SignatureNotificationManager
Manages signature notifications.

**Methods:**
- `notify_signature_required()` - Send signature required notification
- `notify_signature_completed()` - Send signature completed notification
- `notify_document_fully_signed()` - Send document fully signed notification

## Usage Examples

### Creating an Inspection

```python
from inspections.models import VehicleInspection
from listings.models import Vehicle
from accounts.models import Customer, Dealership, Account

# Create inspection
inspection = VehicleInspection.objects.create(
    vehicle=vehicle,
    inspector=inspector_account,
    customer=customer,
    dealer=dealership,
    inspection_type='pre_purchase',
    exterior_data={
        'body_condition': 'good',
        'paint_condition': 'excellent',
        'windshield_condition': 'good'
    },
    interior_data={
        'seats_condition': 'good',
        'dashboard_condition': 'excellent'
    },
    engine_data={
        'engine_condition': 'good',
        'oil_level': 'excellent'
    },
    mechanical_data={
        'transmission_condition': 'good',
        'brakes_condition': 'good'
    },
    safety_data={
        'airbags_condition': 'excellent',
        'seatbelts_condition': 'good'
    },
    inspector_notes='Vehicle is in good overall condition',
    recommended_actions=['Replace brake pads', 'Check tire pressure']
)
```

### Generating a Document

```python
from inspections.services import DocumentManagementService

doc_service = DocumentManagementService()
document = doc_service.create_inspection_document(
    inspection=inspection,
    template_type='standard',
    include_photos=True,
    include_recommendations=True
)
```

### Submitting a Signature

```python
signature_data = {
    'signature_image': 'data:image/png;base64,...',
    'signature_method': 'drawn',
    'coordinates': {'x': 100, 'y': 200, 'width': 200, 'height': 50}
}

signature = doc_service.submit_signature(
    document=document,
    signer_id=user.id,
    signature_data=signature_data,
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...'
)
```

### Searching Documents

```python
from inspections.document_management import DocumentSearchManager

documents = DocumentSearchManager.search_documents(
    user=request.user,
    filters={
        'status': 'signed',
        'date_from': '2024-01-01',
        'vehicle_id': 123
    }
)
```

### Checking Access

```python
from inspections.document_management import DocumentAccessControl

can_download = DocumentAccessControl.can_download(user, document)
if can_download:
    # Allow download
    pass
```

## Security Features

1. **Access Control**: Role-based access control for documents
2. **Signature Validation**: Comprehensive signature validation and verification
3. **Audit Trail**: Complete audit trail for all document operations
4. **Rate Limiting**: Rate limiting for signature submissions
5. **Tamper Detection**: Hash-based tamper detection for signatures and documents
6. **IP Tracking**: IP address tracking for all signature submissions
7. **Expiration**: Document expiration for security
8. **Encryption**: Secure document storage with Cloudinary

## Retention Policies

- **Active Documents**: Retained for 1 year (365 days)
- **Archived Documents**: Retained for 7 years (2555 days)
- **Automatic Archival**: Documents are automatically archived after 1 year
- **Automatic Deletion**: Archived documents are deleted after 7 years

## Admin Tasks

### Running Retention Cleanup

```bash
# Via API (admin only)
POST /api/v1/inspections/management/documents/retention-cleanup/
```

### Viewing Audit Trails

```bash
# Via API
GET /api/v1/inspections/management/documents/{document_id}/audit-trail/
```

## Testing

The system includes comprehensive testing capabilities:

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test end-to-end workflows
3. **API Tests**: Test all API endpoints
4. **Security Tests**: Test access controls and permissions

## Future Enhancements

1. Real-time notifications via WebSocket
2. Advanced analytics and reporting
3. Mobile app integration
4. Blockchain-based signature verification
5. AI-powered inspection analysis
6. Multi-language support expansion
7. Advanced document templates
8. Integration with external compliance systems

## Support

For issues or questions, please contact the development team or refer to the main project documentation.
