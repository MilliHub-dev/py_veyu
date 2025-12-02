# Support Ticket API Documentation

## Overview
The Support Ticket API allows customers to create and manage support tickets, and enables staff to respond to and resolve customer issues through a ticketing system with integrated live chat.

## Base URL
```
/api/v1/support/
```

## Authentication
All endpoints require authentication via JWT token or session authentication.

---

## Endpoints

### 1. List Tickets
**GET** `/api/v1/support/tickets/`

List all support tickets. Customers see only their own tickets, staff see all tickets.

**Query Parameters:**
- `status` (optional): Filter by status (`open`, `in-progress`, `awaiting-user`, `resolved`)
- `severity` (optional): Filter by severity (`high`, `moderate`, `low`)
- `category` (optional): Filter by category UUID
- `assigned_to_me` (optional, staff only): `true` to see only tickets assigned to you
- `overdue` (optional): `true` to see only overdue tickets
- `page` (optional): Page number for pagination
- `page_size` (optional): Number of results per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 45,
  "next": "http://api.veyu.cc/api/v1/support/tickets/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "customer": 5,
      "customer_name": "John Doe",
      "customer_email": "john@example.com",
      "status": "open",
      "status_display": "Open",
      "severity_level": "high",
      "severity_display": "High Severity",
      "subject": "Unable to complete payment",
      "tags": [
        {
          "id": 1,
          "uuid": "...",
          "name": "Payment Issue",
          "date_created": "2024-01-15T10:30:00Z"
        }
      ],
      "category": {
        "id": 2,
        "uuid": "...",
        "name": "Billing",
        "total_tickets": 12,
        "date_created": "2024-01-01T00:00:00Z"
      },
      "chat_room": "abc123-room-uuid",
      "correspondents": [
        {
          "id": 10,
          "name": "Support Agent",
          "email": "agent@veyu.cc"
        }
      ],
      "days_open": 2,
      "is_overdue": true,
      "total_correspondents": 1,
      "date_created": "2024-01-15T10:30:00Z",
      "date_updated": "2024-01-16T14:20:00Z"
    }
  ]
}
```

---

### 2. Create Ticket
**POST** `/api/v1/support/tickets/`

Create a new support ticket. Only customers can create tickets.

**Request Body:**
```json
{
  "subject": "Unable to complete payment",
  "severity_level": "high",
  "tag_ids": [1, 3],
  "category_id": 2
}
```

**Fields:**
- `subject` (required): Title/description of the issue
- `severity_level` (required): `high`, `moderate`, or `low`
- `tag_ids` (optional): Array of tag IDs
- `category_id` (optional): Category ID

**Response:** `201 Created`
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "customer": 5,
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "status": "open",
  "status_display": "Open",
  "severity_level": "high",
  "severity_display": "High Severity",
  "subject": "Unable to complete payment",
  "tags": [...],
  "category": {...},
  "chat_room": "abc123-room-uuid",
  "correspondents": [],
  "days_open": 0,
  "is_overdue": false,
  "total_correspondents": 0,
  "date_created": "2024-01-15T10:30:00Z",
  "date_updated": "2024-01-15T10:30:00Z"
}
```

---

### 3. Get Ticket Details
**GET** `/api/v1/support/tickets/{id}/`

Retrieve details of a specific ticket.

**Response:** `200 OK`
```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "customer": 5,
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "status": "open",
  "status_display": "Open",
  "severity_level": "high",
  "severity_display": "High Severity",
  "subject": "Unable to complete payment",
  "tags": [...],
  "category": {...},
  "chat_room": "abc123-room-uuid",
  "correspondents": [...],
  "days_open": 2,
  "is_overdue": true,
  "total_correspondents": 1,
  "date_created": "2024-01-15T10:30:00Z",
  "date_updated": "2024-01-16T14:20:00Z"
}
```

---

### 4. Update Ticket
**PUT/PATCH** `/api/v1/support/tickets/{id}/`

Update a ticket. Only staff can update tickets.

**Request Body (PATCH):**
```json
{
  "status": "in-progress",
  "severity_level": "moderate",
  "tag_ids": [1, 2, 3],
  "category_id": 2,
  "correspondent_ids": [10, 15]
}
```

**Fields (all optional for PATCH):**
- `status`: `open`, `in-progress`, `awaiting-user`, or `resolved`
- `severity_level`: `high`, `moderate`, or `low`
- `subject`: Update the ticket subject
- `tag_ids`: Array of tag IDs
- `category_id`: Category ID
- `correspondent_ids`: Array of staff user IDs to assign

**Response:** `200 OK`

---

### 5. Delete Ticket
**DELETE** `/api/v1/support/tickets/{id}/`

Delete a ticket. Only staff can delete tickets.

**Response:** `204 No Content`

---

### 6. Assign Staff to Ticket
**POST** `/api/v1/support/tickets/{id}/assign_staff/`

Assign staff members to a ticket. Only staff can perform this action.

**Request Body:**
```json
{
  "staff_ids": [10, 15, 20]
}
```

**Response:** `200 OK`
Returns the updated ticket with new correspondents added.

---

### 7. Remove Staff from Ticket
**POST** `/api/v1/support/tickets/{id}/remove_staff/`

Remove staff members from a ticket. Only staff can perform this action.

**Request Body:**
```json
{
  "staff_ids": [15]
}
```

**Response:** `200 OK`
Returns the updated ticket with correspondents removed.

---

### 8. List Tags
**GET** `/api/v1/support/tags/`

Get all available ticket tags.

**Response:**
```json
[
  {
    "id": 1,
    "uuid": "...",
    "name": "Bug",
    "date_created": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "uuid": "...",
    "name": "Feature Request",
    "date_created": "2024-01-01T00:00:00Z"
  }
]
```

---

### 9. Create Tag
**POST** `/api/v1/support/tags/create/`

Create a new tag. Only staff can create tags.

**Request Body:**
```json
{
  "name": "Customer Reported Error"
}
```

**Response:** `201 Created`

---

### 10. List Categories
**GET** `/api/v1/support/categories/`

Get all ticket categories.

**Response:**
```json
[
  {
    "id": 1,
    "uuid": "...",
    "name": "Technical Support",
    "total_tickets": 45,
    "date_created": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "uuid": "...",
    "name": "Billing",
    "total_tickets": 12,
    "date_created": "2024-01-01T00:00:00Z"
  }
]
```

---

### 11. Create Category
**POST** `/api/v1/support/categories/create/`

Create a new category. Only staff can create categories.

**Request Body:**
```json
{
  "name": "Account Issues"
}
```

**Response:** `201 Created`

---

### 12. Ticket Statistics
**GET** `/api/v1/support/stats/`

Get ticket statistics. Only staff can view statistics.

**Response:**
```json
{
  "total": 150,
  "open": 45,
  "in_progress": 30,
  "awaiting_user": 15,
  "resolved": 60,
  "high_severity": 20,
  "moderate_severity": 50,
  "low_severity": 80,
  "overdue": 12
}
```

---

## Live Chat Integration

Each ticket has an associated chat room. To connect to the live chat:

**WebSocket URL:**
```
ws://your-domain/ws/support/{ticket_id}/?token={auth_token}
```

**Message Format:**
```json
{
  "message": "Hello, I need help with my payment"
}
```

See the Chat API documentation for more details on WebSocket communication.

---

## Status Workflow

Typical ticket lifecycle:
1. **open** - Customer creates ticket
2. **in-progress** - Staff is working on the issue
3. **awaiting-user** - Waiting for customer response
4. **resolved** - Issue is resolved

---

## Severity Levels & SLA

- **High Severity**: Overdue after 1 day
- **Moderate Severity**: Overdue after 3 days
- **Low Severity**: Overdue after 7 days

The `is_overdue` field automatically calculates if a ticket needs attention based on these rules.

---

## Permissions

- **Customers**: Can create tickets and view their own tickets
- **Staff**: Can view all tickets, update status, assign staff, and manage tags/categories

---

## Error Responses

**403 Forbidden:**
```json
{
  "error": "Only staff can update support tickets"
}
```

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

**400 Bad Request:**
```json
{
  "subject": ["This field is required."],
  "severity_level": ["Invalid choice."]
}
```
