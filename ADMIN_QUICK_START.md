# Admin Quick Start Guide

## Accessing the Enhanced Inspection Admin

### 1. Create a Superuser (if you haven't already)
```bash
python manage.py createsuperuser
```
Follow the prompts to create your admin account.

### 2. Access the Admin Interface
Open your browser and go to:
```
http://127.0.0.1:8000/admin/
```

### 3. Login
Use the superuser credentials you just created.

### 4. Navigate to Inspections

Once logged in, you'll see the admin dashboard. Look for the **INSPECTIONS** section with these options:

#### **Vehicle Inspections**
- URL: `http://127.0.0.1:8000/admin/inspections/vehicleinspection/`
- View all inspections with document counts
- Click any inspection to see related documents with view/download links

#### **Inspection Documents** ⭐ (Main place to view signed slips)
- URL: `http://127.0.0.1:8000/admin/inspections/inspectiondocument/`
- See all generated documents
- Signature status badges show completion
- Direct view and download buttons in list view
- Click any document for detailed signature information

#### **Digital Signatures**
- URL: `http://127.0.0.1:8000/admin/inspections/digitalsignature/`
- View all signatures with preview images
- See audit trail (IP, timestamp, user agent)
- Verification status for each signature

#### **Inspection Photos**
- URL: `http://127.0.0.1:8000/admin/inspections/inspectionphoto/`
- View all uploaded inspection photos

#### **Inspection Templates**
- URL: `http://127.0.0.1:8000/admin/inspections/inspectiontemplate/`
- Manage PDF templates

## Key Features

### 🎯 Quick Actions
- **View Document**: Click the blue "📄 View Document" button
- **Download Document**: Click the green "⬇️ Download" button
- **Check Signatures**: Look for colored badges (Green ✓ = fully signed)

### 🔍 Filtering
Use the right sidebar to filter by:
- Status (signed, pending, etc.)
- Template type
- Date range
- Signature status

### 🔎 Searching
Use the search bar to find:
- Vehicle names
- Inspector names
- Customer emails
- Document IDs

## Visual Guide

### Signature Status Badges
- 🟢 **✓ Fully Signed**: All required signatures collected
- 🟠 **◐ Partially Signed**: Some signatures pending
- 🔴 **○ Pending Signatures**: No signatures yet

### Document Status
- **Signed**: Document is complete and fully signed
- **Ready for Signature**: Document generated, awaiting signatures
- **Generating**: Document is being created
- **Archived**: Document has been archived

## Example Workflow

1. **Find a signed inspection slip:**
   - Go to Inspection Documents
   - Filter by Status: "Signed"
   - Look for green ✓ badge
   - Click "View Document" to open PDF

2. **Check signature details:**
   - Click on the document ID
   - Scroll to "Signature Summary" section
   - See who signed, when, and how

3. **Download for records:**
   - Click the green "Download" button
   - PDF will be saved to your downloads folder

## Troubleshooting

### Can't see any data?
- The database is fresh (SQLite)
- You need to create test data via API or Django shell
- Or wait for real inspections to be created

### Documents not showing?
- Check if inspections have been completed
- Documents are only generated after inspection completion
- Use the API to generate test documents

### Signature images not displaying?
- Ensure Cloudinary is configured in settings
- Check that signature images were uploaded correctly
- Verify file permissions

## API Endpoints for Testing

Create test data using these endpoints:

```bash
# Create inspection
POST http://127.0.0.1:8000/api/v1/inspections/

# Generate document
POST http://127.0.0.1:8000/api/v1/inspections/{id}/generate-document/

# Submit signature
POST http://127.0.0.1:8000/api/v1/inspections/documents/{id}/sign/
```

See `api.md` for complete API documentation.

## Support

For more details:
- Full API documentation: `api.md`
- Admin features guide: `inspections/ADMIN_FEATURES.md`
- Implementation summary: `inspections/IMPLEMENTATION_SUMMARY.md`

---

**Server URL:** http://127.0.0.1:8000/
**Admin URL:** http://127.0.0.1:8000/admin/
**API Docs:** http://127.0.0.1:8000/api/docs/
