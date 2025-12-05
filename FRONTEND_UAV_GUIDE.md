# Frontend Guide: UAV (Drone) Integration

## Overview
This guide covers how to integrate UAV/Drone listings into your frontend application, including creating, displaying, and filtering drone listings.

## UAV Data Structure

### UAV Vehicle Object

```typescript
interface UAVVehicle {
  kind: 'uav';
  uuid: string;
  name: string;
  brand: string;
  model: string;
  condition: 'new' | 'used-foreign' | 'used-local';
  color: string;
  available: boolean;
  
  // UAV-specific fields
  registration_number?: string;
  uav_type?: 'quadcopter' | 'hexacopter' | 'octocopter' | 'fixed-wing' | 'hybrid';
  purpose?: 'recreational' | 'photography' | 'surveying' | 'agriculture' | 
            'delivery' | 'inspection' | 'racing' | 'military';
  max_flight_time?: number;      // minutes
  max_range?: number;             // kilometers
  max_altitude?: number;          // meters
  max_speed?: number;             // km/h
  camera_resolution?: string;     // e.g., "4K", "8K"
  payload_capacity?: number;      // kg
  weight?: number;                // kg
  rotor_count?: number;
  has_obstacle_avoidance: boolean;
  has_gps: boolean;
  has_return_to_home: boolean;
  
  // Common fields
  images: Array<{ id: number; uuid: string; url: string }>;
  features: string[];
  dealer: DealerInfo;
}

interface UAVListing {
  uuid: string;
  title: string;
  listing_type: 'sale' | 'rental';
  price: number;
  payment_cycle?: string;
  vehicle: UAVVehicle;
  total_views: number;
  date_listed: string;
}
```

## Creating UAV Listings

### Create Listing Form (React)

```jsx
import React, { useState } from 'react';

const CreateUAVListing = () => {
  const [formData, setFormData] = useState({
    action: 'create-listing',
    vehicle_type: 'uav',
    title: '',
    brand: '',
    model: '',
    condition: 'new',
    listing_type: 'sale',
    price: '',
    color: '',
    
    // UAV-specific
    registration_number: '',
    uav_type: 'quadcopter',
    purpose: 'photography',
    max_flight_time: '',
    max_range: '',
    max_altitude: '',
    max_speed: '',
    camera_resolution: '',
    payload_capacity: '',
    weight: '',
    rotor_count: 4,
    has_obstacle_avoidance: false,
    has_gps: true,
    has_return_to_home: true,
    
    features: [],
    notes: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/v1/dealership/listings/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (!data.error) {
        console.log('UAV listing created:', data.listing);
        // Redirect or show success message
      }
    } catch (error) {
      console.error('Failed to create listing:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Create UAV Listing</h2>
      
      {/* Basic Information */}
      <section>
        <h3>Basic Information</h3>
        <input
          type="text"
          placeholder="Title"
          value={formData.title}
          onChange={(e) => setFormData({...formData, title: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="Brand (e.g., DJI, Autel)"
          value={formData.brand}
          onChange={(e) => setFormData({...formData, brand: e.target.value})}
          required
        />
        <input
          type="text"
          placeholder="Model"
          value={formData.model}
          onChange={(e) => setFormData({...formData, model: e.target.value})}
          required
        />
      </section>

      
      {/* UAV Specifications */}
      <section>
        <h3>UAV Specifications</h3>
        
        <select
          value={formData.uav_type}
          onChange={(e) => setFormData({...formData, uav_type: e.target.value})}
        >
          <option value="quadcopter">Quadcopter (4 rotors)</option>
          <option value="hexacopter">Hexacopter (6 rotors)</option>
          <option value="octocopter">Octocopter (8 rotors)</option>
          <option value="fixed-wing">Fixed-Wing</option>
          <option value="hybrid">Hybrid VTOL</option>
        </select>
        
        <select
          value={formData.purpose}
          onChange={(e) => setFormData({...formData, purpose: e.target.value})}
        >
          <option value="recreational">Recreational</option>
          <option value="photography">Photography/Videography</option>
          <option value="surveying">Surveying/Mapping</option>
          <option value="agriculture">Agriculture</option>
          <option value="delivery">Delivery</option>
          <option value="inspection">Industrial Inspection</option>
          <option value="racing">Racing</option>
          <option value="military">Military/Defense</option>
        </select>
        
        <input
          type="number"
          placeholder="Max Flight Time (minutes)"
          value={formData.max_flight_time}
          onChange={(e) => setFormData({...formData, max_flight_time: e.target.value})}
        />
        
        <input
          type="number"
          placeholder="Max Range (km)"
          value={formData.max_range}
          onChange={(e) => setFormData({...formData, max_range: e.target.value})}
        />
        
        <input
          type="text"
          placeholder="Camera Resolution (e.g., 4K, 8K)"
          value={formData.camera_resolution}
          onChange={(e) => setFormData({...formData, camera_resolution: e.target.value})}
        />
      </section>
      
      {/* Features */}
      <section>
        <h3>Features</h3>
        <label>
          <input
            type="checkbox"
            checked={formData.has_obstacle_avoidance}
            onChange={(e) => setFormData({...formData, has_obstacle_avoidance: e.target.checked})}
          />
          Obstacle Avoidance
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.has_gps}
            onChange={(e) => setFormData({...formData, has_gps: e.target.checked})}
          />
          GPS
        </label>
        <label>
          <input
            type="checkbox"
            checked={formData.has_return_to_home}
            onChange={(e) => setFormData({...formData, has_return_to_home: e.target.checked})}
          />
          Return to Home
        </label>
      </section>
      
      {/* Pricing */}
      <section>
        <h3>Pricing</h3>
        <select
          value={formData.listing_type}
          onChange={(e) => setFormData({...formData, listing_type: e.target.value})}
        >
          <option value="sale">For Sale</option>
          <option value="rental">For Rent</option>
        </select>
        
        <input
          type="number"
          placeholder="Price (₦)"
          value={formData.price}
          onChange={(e) => setFormData({...formData, price: e.target.value})}
          required
        />
      </section>
      
      <button type="submit">Create Listing</button>
    </form>
  );
};

export default CreateUAVListing;
```

## Displaying UAV Listings

### UAV Card Component

```jsx
const UAVCard = ({ listing }) => {
  const { vehicle } = listing;
  
  const getUAVTypeIcon = (type) => {
    const icons = {
      quadcopter: '🚁',
      hexacopter: '🚁',
      octocopter: '🚁',
      'fixed-wing': '✈️',
      hybrid: '🛸'
    };
    return icons[type] || '🚁';
  };

  return (
    <div className="uav-card">
      <div className="card-image">
        <img 
          src={vehicle.images[0]?.url || '/placeholder-drone.jpg'} 
          alt={listing.title} 
        />
        <span className="type-badge">
          {getUAVTypeIcon(vehicle.uav_type)} {vehicle.uav_type}
        </span>
      </div>
      
      <div className="card-content">
        <h3>{listing.title}</h3>
        <p className="brand">{vehicle.brand} {vehicle.model}</p>
        
        <div className="specs-grid">
          {vehicle.max_flight_time && (
            <div className="spec">
              <span className="icon">🕐</span>
              <span>{vehicle.max_flight_time} min</span>
            </div>
          )}
          
          {vehicle.max_range && (
            <div className="spec">
              <span className="icon">📏</span>
              <span>{vehicle.max_range} km</span>
            </div>
          )}
          
          {vehicle.camera_resolution && (
            <div className="spec">
              <span className="icon">📷</span>
              <span>{vehicle.camera_resolution}</span>
            </div>
          )}
          
          {vehicle.weight && (
            <div className="spec">
              <span className="icon">⚖️</span>
              <span>{vehicle.weight} kg</span>
            </div>
          )}
        </div>
        
        <div className="features">
          {vehicle.has_obstacle_avoidance && (
            <span className="feature-badge">🛡️ Obstacle Avoidance</span>
          )}
          {vehicle.has_gps && (
            <span className="feature-badge">📍 GPS</span>
          )}
          {vehicle.has_return_to_home && (
            <span className="feature-badge">🏠 RTH</span>
          )}
        </div>
        
        <div className="card-footer">
          <span className="price">₦{listing.price.toLocaleString()}</span>
          <button className="view-btn">View Details</button>
        </div>
      </div>
    </div>
  );
};
```

### UAV Detail Page

```jsx
const UAVDetailPage = ({ listingId }) => {
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchListing();
  }, [listingId]);

  const fetchListing = async () => {
    try {
      const response = await fetch(`/api/v1/listings/buy/${listingId}/`);
      const data = await response.json();
      setListing(data.data.listing);
    } catch (error) {
      console.error('Failed to fetch listing:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!listing) return <div>Listing not found</div>;

  const { vehicle } = listing;

  return (
    <div className="uav-detail-page">
      <div className="image-gallery">
        {vehicle.images.map((img, index) => (
          <img key={index} src={img.url} alt={`${listing.title} ${index + 1}`} />
        ))}
      </div>
      
      <div className="detail-content">
        <h1>{listing.title}</h1>
        <p className="brand">{vehicle.brand} {vehicle.model}</p>
        <div className="price">₦{listing.price.toLocaleString()}</div>
        
        <div className="specifications">
          <h2>Specifications</h2>
          
          <div className="spec-section">
            <h3>Type & Purpose</h3>
            <div className="spec-row">
              <span className="label">UAV Type:</span>
              <span className="value">{vehicle.uav_type}</span>
            </div>
            <div className="spec-row">
              <span className="label">Purpose:</span>
              <span className="value">{vehicle.purpose}</span>
            </div>
            {vehicle.rotor_count && (
              <div className="spec-row">
                <span className="label">Rotors:</span>
                <span className="value">{vehicle.rotor_count}</span>
              </div>
            )}
          </div>
          
          <div className="spec-section">
            <h3>Performance</h3>
            {vehicle.max_flight_time && (
              <div className="spec-row">
                <span className="label">Max Flight Time:</span>
                <span className="value">{vehicle.max_flight_time} minutes</span>
              </div>
            )}
            {vehicle.max_range && (
              <div className="spec-row">
                <span className="label">Max Range:</span>
                <span className="value">{vehicle.max_range} km</span>
              </div>
            )}
            {vehicle.max_altitude && (
              <div className="spec-row">
                <span className="label">Max Altitude:</span>
                <span className="value">{vehicle.max_altitude} meters</span>
              </div>
            )}
            {vehicle.max_speed && (
              <div className="spec-row">
                <span className="label">Max Speed:</span>
                <span className="value">{vehicle.max_speed} km/h</span>
              </div>
            )}
          </div>
          
          <div className="spec-section">
            <h3>Camera & Payload</h3>
            {vehicle.camera_resolution && (
              <div className="spec-row">
                <span className="label">Camera:</span>
                <span className="value">{vehicle.camera_resolution}</span>
              </div>
            )}
            {vehicle.payload_capacity && (
              <div className="spec-row">
                <span className="label">Payload Capacity:</span>
                <span className="value">{vehicle.payload_capacity} kg</span>
              </div>
            )}
            {vehicle.weight && (
              <div className="spec-row">
                <span className="label">Weight:</span>
                <span className="value">{vehicle.weight} kg</span>
              </div>
            )}
          </div>
          
          <div className="spec-section">
            <h3>Features</h3>
            <div className="features-list">
              <div className={`feature ${vehicle.has_obstacle_avoidance ? 'available' : 'unavailable'}`}>
                {vehicle.has_obstacle_avoidance ? '✅' : '❌'} Obstacle Avoidance
              </div>
              <div className={`feature ${vehicle.has_gps ? 'available' : 'unavailable'}`}>
                {vehicle.has_gps ? '✅' : '❌'} GPS Navigation
              </div>
              <div className={`feature ${vehicle.has_return_to_home ? 'available' : 'unavailable'}`}>
                {vehicle.has_return_to_home ? '✅' : '❌'} Return to Home
              </div>
            </div>
          </div>
        </div>
        
        <div className="dealer-info">
          <h3>Seller Information</h3>
          <p>{vehicle.dealer.business_name}</p>
          <button>Contact Dealer</button>
        </div>
      </div>
    </div>
  );
};
```


## Filtering UAVs

### UAV-Specific Filter Component

```jsx
const UAVFilters = ({ onFilterChange }) => {
  const [filters, setFilters] = useState({
    uavTypes: [],
    purposes: [],
    minFlightTime: '',
    maxPrice: '',
    hasObstacleAvoidance: false,
    hasGPS: false
  });

  const uavTypes = [
    { value: 'quadcopter', label: 'Quadcopter' },
    { value: 'hexacopter', label: 'Hexacopter' },
    { value: 'octocopter', label: 'Octocopter' },
    { value: 'fixed-wing', label: 'Fixed-Wing' },
    { value: 'hybrid', label: 'Hybrid VTOL' }
  ];

  const purposes = [
    { value: 'recreational', label: 'Recreational' },
    { value: 'photography', label: 'Photography' },
    { value: 'surveying', label: 'Surveying' },
    { value: 'agriculture', label: 'Agriculture' },
    { value: 'delivery', label: 'Delivery' },
    { value: 'inspection', label: 'Inspection' },
    { value: 'racing', label: 'Racing' }
  ];

  const handleApplyFilters = () => {
    onFilterChange(filters);
  };

  return (
    <div className="uav-filters">
      <h3>Filter Drones</h3>
      
      <div className="filter-group">
        <label>UAV Type</label>
        {uavTypes.map(type => (
          <label key={type.value} className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.uavTypes.includes(type.value)}
              onChange={(e) => {
                const newTypes = e.target.checked
                  ? [...filters.uavTypes, type.value]
                  : filters.uavTypes.filter(t => t !== type.value);
                setFilters({...filters, uavTypes: newTypes});
              }}
            />
            {type.label}
          </label>
        ))}
      </div>
      
      <div className="filter-group">
        <label>Purpose</label>
        {purposes.map(purpose => (
          <label key={purpose.value} className="checkbox-label">
            <input
              type="checkbox"
              checked={filters.purposes.includes(purpose.value)}
              onChange={(e) => {
                const newPurposes = e.target.checked
                  ? [...filters.purposes, purpose.value]
                  : filters.purposes.filter(p => p !== purpose.value);
                setFilters({...filters, purposes: newPurposes});
              }}
            />
            {purpose.label}
          </label>
        ))}
      </div>
      
      <div className="filter-group">
        <label>Min Flight Time (minutes)</label>
        <input
          type="number"
          value={filters.minFlightTime}
          onChange={(e) => setFilters({...filters, minFlightTime: e.target.value})}
          placeholder="e.g., 30"
        />
      </div>
      
      <div className="filter-group">
        <label>Max Price (₦)</label>
        <input
          type="number"
          value={filters.maxPrice}
          onChange={(e) => setFilters({...filters, maxPrice: e.target.value})}
          placeholder="e.g., 5000000"
        />
      </div>
      
      <div className="filter-group">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={filters.hasObstacleAvoidance}
            onChange={(e) => setFilters({...filters, hasObstacleAvoidance: e.target.checked})}
          />
          Must have Obstacle Avoidance
        </label>
        
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={filters.hasGPS}
            onChange={(e) => setFilters({...filters, hasGPS: e.target.checked})}
          />
          Must have GPS
        </label>
      </div>
      
      <button onClick={handleApplyFilters} className="apply-filters-btn">
        Apply Filters
      </button>
    </div>
  );
};
```

## Popular UAV Brands

### Brand Data for Autocomplete

```javascript
export const uavBrands = [
  {
    name: 'DJI',
    logo: '/brands/dji.png',
    popular: true,
    models: ['Mavic 3', 'Mavic Air 2', 'Mini 3 Pro', 'Phantom 4', 'Inspire 2', 'Matrice 300']
  },
  {
    name: 'Autel Robotics',
    logo: '/brands/autel.png',
    popular: true,
    models: ['EVO II', 'EVO Lite', 'EVO Nano']
  },
  {
    name: 'Parrot',
    logo: '/brands/parrot.png',
    popular: false,
    models: ['Anafi', 'Anafi USA', 'Bebop 2']
  },
  {
    name: 'Skydio',
    logo: '/brands/skydio.png',
    popular: true,
    models: ['Skydio 2', 'Skydio X2']
  },
  {
    name: 'Yuneec',
    logo: '/brands/yuneec.png',
    popular: false,
    models: ['Typhoon H', 'Mantis G']
  },
  {
    name: 'Holy Stone',
    logo: '/brands/holystone.png',
    popular: false,
    models: ['HS720', 'HS110D']
  }
];

// Brand selector component
const UAVBrandSelector = ({ onSelect }) => {
  const [search, setSearch] = useState('');
  
  const filteredBrands = uavBrands.filter(brand =>
    brand.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="brand-selector">
      <input
        type="text"
        placeholder="Search brands..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      
      <div className="popular-brands">
        <h4>Popular Brands</h4>
        <div className="brand-grid">
          {uavBrands.filter(b => b.popular).map(brand => (
            <button
              key={brand.name}
              className="brand-card"
              onClick={() => onSelect(brand.name)}
            >
              <img src={brand.logo} alt={brand.name} />
              <span>{brand.name}</span>
            </button>
          ))}
        </div>
      </div>
      
      <div className="all-brands">
        <h4>All Brands</h4>
        <ul>
          {filteredBrands.map(brand => (
            <li key={brand.name} onClick={() => onSelect(brand.name)}>
              {brand.name}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

## Validation

### Form Validation Helper

```javascript
export const validateUAVListing = (formData) => {
  const errors = {};

  // Required fields
  if (!formData.title) errors.title = 'Title is required';
  if (!formData.brand) errors.brand = 'Brand is required';
  if (!formData.model) errors.model = 'Model is required';
  if (!formData.price || formData.price <= 0) {
    errors.price = 'Valid price is required';
  }

  // UAV-specific validations
  if (formData.max_flight_time && formData.max_flight_time < 0) {
    errors.max_flight_time = 'Flight time must be positive';
  }
  
  if (formData.max_range && formData.max_range < 0) {
    errors.max_range = 'Range must be positive';
  }
  
  if (formData.weight && formData.weight < 0) {
    errors.weight = 'Weight must be positive';
  }
  
  if (formData.payload_capacity && formData.payload_capacity < 0) {
    errors.payload_capacity = 'Payload capacity must be positive';
  }

  // Rotor count validation based on type
  if (formData.uav_type === 'quadcopter' && formData.rotor_count !== 4) {
    errors.rotor_count = 'Quadcopter must have 4 rotors';
  }
  if (formData.uav_type === 'hexacopter' && formData.rotor_count !== 6) {
    errors.rotor_count = 'Hexacopter must have 6 rotors';
  }
  if (formData.uav_type === 'octocopter' && formData.rotor_count !== 8) {
    errors.rotor_count = 'Octocopter must have 8 rotors';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

// Usage in form
const handleSubmit = (e) => {
  e.preventDefault();
  
  const { isValid, errors } = validateUAVListing(formData);
  
  if (!isValid) {
    setFormErrors(errors);
    return;
  }
  
  // Submit form
  submitListing(formData);
};
```

## Styling Examples

### CSS for UAV Cards

```css
.uav-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  background: white;
}

.uav-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.card-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-badge {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.875rem;
  backdrop-filter: blur(4px);
}

.specs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 16px 0;
}

.spec {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: #666;
}

.spec .icon {
  font-size: 1.25rem;
}

.features {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.feature-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #E3F2FD;
  color: #1976D2;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

.price {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2196F3;
}

.view-btn {
  padding: 8px 16px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.view-btn:hover {
  background: #1976D2;
}
```

## Best Practices

### 1. Image Optimization
```javascript
// Use optimized images for UAVs
const getOptimizedImageUrl = (url, width = 800) => {
  // If using Cloudinary or similar
  return url.replace('/upload/', `/upload/w_${width},c_fill,f_auto,q_auto/`);
};
```

### 2. Feature Icons
```javascript
const featureIcons = {
  obstacle_avoidance: '🛡️',
  gps: '📍',
  return_to_home: '🏠',
  follow_me: '👤',
  waypoint: '📍',
  fpv: '🥽',
  night_vision: '🌙'
};
```

### 3. Unit Conversion
```javascript
// Convert units for international users
const convertUnits = (value, from, to) => {
  const conversions = {
    'kg-lbs': (v) => v * 2.20462,
    'km-miles': (v) => v * 0.621371,
    'm-ft': (v) => v * 3.28084
  };
  
  return conversions[`${from}-${to}`]?.(value) || value;
};
```

## Testing

### Component Test Example

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import UAVCard from './UAVCard';

const mockListing = {
  uuid: '123',
  title: 'DJI Mavic 3',
  price: 2500000,
  vehicle: {
    kind: 'uav',
    brand: 'DJI',
    model: 'Mavic 3',
    uav_type: 'quadcopter',
    max_flight_time: 46,
    max_range: 30,
    camera_resolution: '5.1K',
    has_obstacle_avoidance: true,
    has_gps: true,
    images: [{ url: '/test.jpg' }]
  }
};

describe('UAVCard', () => {
  it('renders UAV information correctly', () => {
    render(<UAVCard listing={mockListing} />);
    
    expect(screen.getByText('DJI Mavic 3')).toBeInTheDocument();
    expect(screen.getByText('46 min')).toBeInTheDocument();
    expect(screen.getByText('30 km')).toBeInTheDocument();
    expect(screen.getByText('5.1K')).toBeInTheDocument();
  });

  it('shows feature badges when available', () => {
    render(<UAVCard listing={mockListing} />);
    
    expect(screen.getByText(/Obstacle Avoidance/)).toBeInTheDocument();
    expect(screen.getByText(/GPS/)).toBeInTheDocument();
  });
});
```

## Resources

- **API Documentation:** `VEHICLE_TYPE_FILTER_UPDATE.md`
- **Backend UAV Guide:** `UAV_VEHICLE_TYPE_UPDATE.md`
- **Filter Guide:** `FRONTEND_VEHICLE_FILTERS_GUIDE.md`
- **Migration:** `MIGRATION_COMMANDS.md`
