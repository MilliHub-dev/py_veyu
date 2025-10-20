# Business Verification - Frontend Quick Start Guide

## 🎯 Quick Overview

**What Changed:**
- Removed Dojah third-party verification
- Added manual admin approval workflow
- New API endpoints for submitting and checking verification status

**Who Can Use:**
- Dealers (`user_type: 'dealer'`)
- Mechanics (`user_type: 'mechanic'`)

---

## 🚀 Quick Integration (5 Steps)

### Step 1: Check Status After Login

```javascript
// After successful login
const loginResponse = await login(email, password);

if (loginResponse.user_type === 'dealer' || loginResponse.user_type === 'mechanic') {
  const status = loginResponse.business_verification_status;
  // status can be: 'not_submitted', 'pending', 'verified', 'rejected'
  
  // Show appropriate UI based on status
  showVerificationBanner(status);
}
```

### Step 2: Create Verification Form

```jsx
// React Example
const VerificationForm = () => {
  const [formData, setFormData] = useState({
    business_type: userType === 'dealer' ? 'dealership' : 'mechanic',
    business_name: '',
    business_address: '',
    business_email: '',
    business_phone: '',
    cac_number: '',
    tin_number: ''
  });

  const [files, setFiles] = useState({
    cac_document: null,
    tin_document: null,
    proof_of_address: null,
    business_license: null
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const formDataToSend = new FormData();
    
    // Add text fields
    Object.entries(formData).forEach(([key, value]) => {
      formDataToSend.append(key, value);
    });
    
    // Add files
    Object.entries(files).forEach(([key, file]) => {
      if (file) formDataToSend.append(key, file);
    });
    
    try {
      const response = await fetch('https://dev.veyu.cc/api/v1/accounts/verify-business/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formDataToSend
      });
      
      const result = await response.json();
      
      if (result.error) {
        // Show validation errors
        setErrors(result.errors);
      } else {
        // Success!
        showSuccessMessage(result.message);
        // Redirect to dashboard or status page
      }
    } catch (error) {
      showErrorMessage('Submission failed. Please try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields here */}
    </form>
  );
};
```

### Step 3: Display Status Badge

```jsx
const VerificationStatusBadge = ({ status }) => {
  const statusConfig = {
    not_submitted: {
      label: 'Not Submitted',
      color: 'gray',
      icon: '⚠️',
      action: 'Submit Verification'
    },
    pending: {
      label: 'Pending Review',
      color: 'orange',
      icon: '⏳',
      message: 'Your verification is being reviewed by our team'
    },
    verified: {
      label: 'Verified',
      color: 'green',
      icon: '✅',
      message: 'Your business is verified!'
    },
    rejected: {
      label: 'Rejected',
      color: 'red',
      icon: '❌',
      action: 'Resubmit Verification'
    }
  };

  const config = statusConfig[status];

  return (
    <div className={`badge badge-${config.color}`}>
      <span>{config.icon} {config.label}</span>
      {config.message && <p>{config.message}</p>}
      {config.action && <button>{config.action}</button>}
    </div>
  );
};
```

### Step 4: Check Status Anytime

```javascript
const checkVerificationStatus = async () => {
  const response = await fetch('https://dev.veyu.cc/api/v1/accounts/verify-business/', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  return {
    status: data.status,
    statusDisplay: data.status_display,
    submissionDate: data.submission_date,
    rejectionReason: data.rejection_reason
  };
};
```

### Step 5: Handle Rejection

```jsx
const RejectionMessage = ({ reason }) => {
  return (
    <div className="rejection-alert">
      <h3>❌ Verification Rejected</h3>
      <p><strong>Reason:</strong> {reason}</p>
      <button onClick={handleResubmit}>
        Resubmit Verification
      </button>
    </div>
  );
};
```

---

## 📋 Required Form Fields

### Text Fields (Required)
```javascript
{
  business_type: 'dealership' | 'mechanic',  // Auto-set based on user type
  business_name: 'ABC Motors Limited',       // Official business name
  business_address: '123 Main St, Lagos',    // Full address
  business_email: 'info@abc.com',            // Business email
  business_phone: '+2348012345678'           // Phone with country code
}
```

### Text Fields (Optional)
```javascript
{
  cac_number: 'RC123456',        // CAC registration number
  tin_number: '12345678-0001'    // Tax ID number
}
```

### File Fields (Optional but Recommended)
```javascript
{
  cac_document: File,         // CAC certificate (PDF/JPG/PNG)
  tin_document: File,         // TIN certificate (PDF/JPG/PNG)
  proof_of_address: File,     // Utility bill or lease (PDF/JPG/PNG)
  business_license: File      // Business license (PDF/JPG/PNG)
}
```

---

## 🎨 CSS Styling Examples

```css
/* Status Badges */
.badge {
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.badge-gray {
  background-color: #f3f4f6;
  color: #6b7280;
}

.badge-orange {
  background-color: #fef3c7;
  color: #d97706;
}

.badge-green {
  background-color: #d1fae5;
  color: #059669;
}

.badge-red {
  background-color: #fee2e2;
  color: #dc2626;
}

/* Rejection Alert */
.rejection-alert {
  background-color: #fef2f2;
  border: 2px solid #fecaca;
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.rejection-alert h3 {
  color: #dc2626;
  margin-bottom: 8px;
}

.rejection-alert button {
  background-color: #dc2626;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  margin-top: 12px;
}
```

---

## 🔄 Status Flow Diagram

```
User Login
    ↓
Check business_verification_status
    ↓
┌───────────────────────────────────────┐
│                                       │
│  not_submitted  →  Show "Submit" CTA  │
│                                       │
│  pending  →  Show "Under Review" msg  │
│                                       │
│  verified  →  Show "Verified" badge   │
│                                       │
│  rejected  →  Show reason + Resubmit  │
│                                       │
└───────────────────────────────────────┘
```

---

## ⚠️ Error Handling

```javascript
const handleVerificationSubmit = async (formData) => {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      switch (response.status) {
        case 400:
          // Validation errors
          showFieldErrors(data.errors);
          break;
        case 401:
          // Unauthorized - redirect to login
          redirectToLogin();
          break;
        case 404:
          // Profile not found
          showError('Business profile not found. Please contact support.');
          break;
        default:
          showError('An error occurred. Please try again.');
      }
      return;
    }
    
    // Success
    showSuccess(data.message);
    updateVerificationStatus('pending');
    
  } catch (error) {
    showError('Network error. Please check your connection.');
  }
};
```

---

## 📱 Mobile-Friendly File Upload

```jsx
const FileUploadInput = ({ label, name, onChange, accept = ".pdf,.jpg,.jpeg,.png" }) => {
  const [preview, setPreview] = useState(null);
  
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file size (5MB max)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB');
        return;
      }
      
      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(file);
      }
      
      onChange(name, file);
    }
  };
  
  return (
    <div className="file-upload">
      <label>{label}</label>
      <input 
        type="file" 
        accept={accept}
        onChange={handleFileChange}
      />
      {preview && <img src={preview} alt="Preview" className="preview" />}
    </div>
  );
};
```

---

## 🧪 Testing Checklist

- [ ] Form displays correctly for dealers
- [ ] Form displays correctly for mechanics
- [ ] All required fields validated
- [ ] File upload works (all formats)
- [ ] File size validation (5MB limit)
- [ ] Success message shows after submission
- [ ] Status badge updates after submission
- [ ] Rejection reason displays correctly
- [ ] Resubmit works after rejection
- [ ] Status persists after page refresh
- [ ] Mobile responsive design
- [ ] Error messages display properly

---

## 🔗 API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/accounts/verify-business/` | GET | Check status |
| `/api/v1/accounts/verify-business/` | POST | Submit verification |
| `/api/v1/accounts/login/` | POST | Login (includes status) |

---

## 📞 Need Help?

- **Full API Docs**: `docs/BUSINESS_VERIFICATION_API.md`
- **Swagger UI**: `https://dev.veyu.cc/swagger/`
- **Backend Team**: Contact for API issues
- **Test Accounts**: 
  - Dealer: `dealer@test.com` / `password123`
  - Mechanic: `mechanic@test.com` / `password123`

---

## ✅ Quick Wins

1. **Show status badge on dashboard** - 5 mins
2. **Add "Submit Verification" button** - 10 mins
3. **Create basic form** - 30 mins
4. **Add file uploads** - 20 mins
5. **Handle rejection messages** - 15 mins

**Total Time**: ~1.5 hours for basic implementation

---

**Ready to start?** Begin with Step 1 (checking status after login) and build from there! 🚀
