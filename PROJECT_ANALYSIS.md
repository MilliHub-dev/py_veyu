# Motaa - Django Project Analysis

## Project Overview
**Motaa** is a comprehensive Django-based mobility platform described as "Redefining Mobility". This is a full-stack marketplace and service platform for automotive services, vehicle rentals, and mechanic bookings.

🌟 **Current Status**: ✅ Successfully Running on http://localhost:8000

## Technology Stack
- **Framework**: Django 5.1.1 with Django REST Framework 3.15.2
- **Database**: SQLite (with existing data in olddb.sqlite3)
- **Real-time**: Django Channels 4.1.0 with Redis for WebSocket support
- **Authentication**: Django Allauth with JWT tokens (SimpleJWT)
- **Payment Integration**: Paystack API integration
- **SMS Services**: Africa's Talking API
- **Admin Interface**: Django Jazzmin (modern admin interface)
- **Documentation**: drf-yasg for API documentation (Swagger/Redoc)
- **ASGI Server**: Daphne for WebSocket and HTTP support

## Core Applications & Features

### 1. **Accounts App** - User Management System
- **Custom User Model**: Email-based authentication with multiple user types
- **User Types**: Admin, Customer, Mechanic, Dealership, Support
- **Authentication**: JWT token-based with social login support
- **Profiles**: Extended user profiles with locations, skills, and verification
- **Features**: OTP verification, password reset, social authentication

### 2. **Bookings App** - Service Management
- **Service Booking System**: Emergency and routine automotive services
- **Booking Statuses**: requested → accepted/declined → working → completed
- **Service Types**: 
  - Emergency Assistance
  - Routine Checks and Maintenance
- **Workflow**: Customer requests → Mechanic responds → Service delivery → Payment
- **Integration**: Connected with chat system for real-time communication

### 3. **Listings App** - Vehicle Marketplace
- **Vehicle Listings**: New and used vehicles (foreign/local)
- **Payment Cycles**: Single, daily, weekly, monthly, annual payments
- **Vehicle Features**: Air conditioning, Android Auto, keyless entry, etc.
- **Image Management**: Multiple images per vehicle
- **Search & Filter**: Advanced filtering system
- **Dealership Management**: Dealer-specific vehicle management

### 4. **Wallet App** - Payment System
- **Digital Wallet**: NGN currency support with ledger balance tracking
- **Transaction Types**: 
  - Deposits and withdrawals
  - Transfers between wallets
  - Service payments and charges
- **Security**: Locked transactions for escrow services
- **Paystack Integration**: For payment processing

### 5. **Chat App** - Real-time Communication
- **WebSocket Support**: Real-time messaging between users
- **Chat Rooms**: Linked to service bookings
- **Django Channels**: For real-time features

### 6. **Utils App** - Core Utilities
- **Custom Admin**: Enhanced admin interface (veyu_admin)
- **Base Models**: DbModel with common fields (created_at, updated_at, etc.)
- **Helper Functions**: OTP generation, utility functions

## API Endpoints Structure

### Core API Routes (api/v1/):
- **Authentication**: `/token/`, `/token/refresh/`, `/token/verify/`
- **Accounts**: `/accounts/` - User management and profiles
- **Mechanics**: `/mechanics/` - Mechanic services and bookings
- **Listings**: `/listings/` - Vehicle marketplace
- **Chat**: `/chat/` - Real-time messaging
- **Wallet**: `/wallet/` - Payment and wallet management
- **Admin Routes**: 
  - `/admin/mechanics/` - Mechanic administration
  - `/admin/dealership/` - Dealership management

### Documentation:
- **Swagger UI**: `/api/docs/` - Interactive API documentation
- **Redoc**: `/redoc/` - Alternative API documentation

## Database Structure
- **SQLite Database**: Pre-populated with existing data (olddb.sqlite3)
- **Migration System**: Uses Django migrations (currently bypassed due to circular dependencies)
- **Related Models**: Complex relationships between users, vehicles, bookings, and transactions

## Development Environment
- **Python**: 3.13+ with virtual environment setup
- **Dependencies**: All requirements installed via requirements.txt
- **Environment Variables**: Configured via .env file
- **Debug Mode**: Currently running in development mode

## Key Features Implemented
1. **Multi-tenant User System**: Customers, mechanics, dealerships, admins
2. **Service Marketplace**: Book automotive services with real-time tracking
3. **Vehicle Marketplace**: Buy/rent vehicles with flexible payment options
4. **Digital Wallet**: Secure payment processing with escrow functionality
5. **Real-time Chat**: WebSocket-based communication system
6. **Admin Dashboard**: Custom admin interface for platform management
7. **API Documentation**: Comprehensive Swagger/Redoc documentation
8. **Payment Integration**: Paystack for Nigerian market
9. **SMS Integration**: Africa's Talking for notifications

## Architecture Highlights
- **Clean Architecture**: Separated concerns with dedicated apps
- **RESTful API**: Well-structured API with proper namespacing
- **Real-time Capabilities**: WebSocket support for live features
- **Security**: JWT authentication, environment-based configuration
- **Scalability**: ASGI support for concurrent connections
- **Payment Security**: Escrow system with locked transactions

## Business Model
Motaa appears to be a **mobility-as-a-service platform** that:
1. Connects customers with automotive service providers (mechanics)
2. Facilitates vehicle sales and rentals through dealerships
3. Provides a digital wallet system for seamless transactions
4. Enables real-time communication between service providers and customers
5. Takes transaction fees through the platform

This is a sophisticated, production-ready platform for the automotive services industry, particularly targeted at the Nigerian market based on the Paystack integration and NGN currency support.