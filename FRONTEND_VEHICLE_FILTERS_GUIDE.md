# Frontend Guide: Vehicle Type Filters

## Overview
This guide covers how to implement vehicle type filtering in your frontend application, including the new UAV (drone) support.

## Supported Vehicle Types

| Type | Value | Description |
|------|-------|-------------|
| Cars | `car` | Standard automobiles |
| Boats | `boat` | Watercraft and vessels |
| Planes | `plane` | Aircraft |
| Bikes | `bike` | Motorcycles |
| UAVs | `uav` or `drone` | Drones and unmanned aerial vehicles |

## API Endpoints

### Get Listings with Filters

**Sale Listings:**
```
GET /api/v1/listings/buy/
```

**Rental Listings:**
```
GET /api/v1/listings/rent/
```

**Search All Listings:**
```
GET /api/v1/listings/search/
```

## Query Parameters

### Vehicle Type Filter
- **Parameter:** `vehicle_type`
- **Type:** String (comma-separated)
- **Values:** `car`, `boat`, `plane`, `bike`, `uav`, `drone`
- **Example:** `?vehicle_type=car,bike,uav`

### Other Available Filters
- `brands` - Comma-separated brand names (e.g., `Toyota,Honda,DJI`)
- `transmission` - `auto` or `manual`
- `fuel_system` - `diesel`, `electric`, `petrol`, `hybrid`
- `price` - Price range as `min-max` (e.g., `1000000-5000000`)
- `find` - Search term for name/brand/model
- `ordering` - Sort field (e.g., `-created_at`, `price`)


## JavaScript/TypeScript Examples

### Basic Filter Implementation

```javascript
// Fetch cars only
const fetchCars = async () => {
  const response = await fetch('/api/v1/listings/buy/?vehicle_type=car');
  const data = await response.json();
  return data.data.results;
};

// Fetch multiple vehicle types
const fetchVehicles = async (types) => {
  const typeParam = types.join(',');
  const response = await fetch(`/api/v1/listings/buy/?vehicle_type=${typeParam}`);
  const data = await response.json();
  return data.data.results;
};

// Example usage
const vehicles = await fetchVehicles(['car', 'bike', 'uav']);
```

### React Hook Example

```typescript
import { useState, useEffect } from 'react';

interface VehicleFilters {
  vehicleTypes: string[];
  brands?: string[];
  priceRange?: { min: number; max: number };
  transmission?: string;
}

const useVehicleListings = (filters: VehicleFilters) => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchListings = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        
        // Add vehicle type filter
        if (filters.vehicleTypes.length > 0) {
          params.append('vehicle_type', filters.vehicleTypes.join(','));
        }
        
        // Add brand filter
        if (filters.brands && filters.brands.length > 0) {
          params.append('brands', filters.brands.join(','));
        }
        
        // Add price range
        if (filters.priceRange) {
          const { min, max } = filters.priceRange;
          params.append('price', `${min}-${max}`);
        }
        
        // Add transmission
        if (filters.transmission) {
          params.append('transmission', filters.transmission);
        }

        const response = await fetch(`/api/v1/listings/buy/?${params}`);
        const data = await response.json();
        
        setListings(data.data.results);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchListings();
  }, [filters]);

  return { listings, loading, error };
};

// Usage in component
const VehicleList = () => {
  const { listings, loading } = useVehicleListings({
    vehicleTypes: ['car', 'uav'],
    brands: ['Toyota', 'DJI'],
    priceRange: { min: 1000000, max: 5000000 }
  });

  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      {listings.map(listing => (
        <VehicleCard key={listing.uuid} listing={listing} />
      ))}
    </div>
  );
};
```


### Vue.js Composition API Example

```vue
<script setup>
import { ref, computed, watch } from 'vue';

const selectedTypes = ref(['car', 'bike', 'uav']);
const selectedBrands = ref([]);
const priceMin = ref(0);
const priceMax = ref(10000000);
const listings = ref([]);
const loading = ref(false);

const fetchListings = async () => {
  loading.value = true;
  
  const params = new URLSearchParams();
  
  if (selectedTypes.value.length > 0) {
    params.append('vehicle_type', selectedTypes.value.join(','));
  }
  
  if (selectedBrands.value.length > 0) {
    params.append('brands', selectedBrands.value.join(','));
  }
  
  if (priceMin.value || priceMax.value) {
    params.append('price', `${priceMin.value}-${priceMax.value}`);
  }
  
  try {
    const response = await fetch(`/api/v1/listings/buy/?${params}`);
    const data = await response.json();
    listings.value = data.data.results;
  } catch (error) {
    console.error('Failed to fetch listings:', error);
  } finally {
    loading.value = false;
  }
};

// Watch for filter changes
watch([selectedTypes, selectedBrands, priceMin, priceMax], () => {
  fetchListings();
}, { immediate: true });
</script>

<template>
  <div>
    <!-- Vehicle Type Filter -->
    <div class="filter-group">
      <h3>Vehicle Type</h3>
      <label v-for="type in ['car', 'boat', 'plane', 'bike', 'uav']" :key="type">
        <input 
          type="checkbox" 
          :value="type" 
          v-model="selectedTypes"
        />
        {{ type.toUpperCase() }}
      </label>
    </div>
    
    <!-- Listings -->
    <div v-if="loading">Loading...</div>
    <div v-else class="listings-grid">
      <VehicleCard 
        v-for="listing in listings" 
        :key="listing.uuid" 
        :listing="listing" 
      />
    </div>
  </div>
</template>
```

### Angular Service Example

```typescript
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface VehicleFilters {
  vehicleTypes?: string[];
  brands?: string[];
  transmission?: string;
  fuelSystem?: string;
  priceMin?: number;
  priceMax?: number;
  search?: string;
}

@Injectable({
  providedIn: 'root'
})
export class VehicleService {
  private apiUrl = '/api/v1/listings';

  constructor(private http: HttpClient) {}

  getListings(type: 'buy' | 'rent', filters: VehicleFilters): Observable<any> {
    let params = new HttpParams();

    if (filters.vehicleTypes && filters.vehicleTypes.length > 0) {
      params = params.set('vehicle_type', filters.vehicleTypes.join(','));
    }

    if (filters.brands && filters.brands.length > 0) {
      params = params.set('brands', filters.brands.join(','));
    }

    if (filters.transmission) {
      params = params.set('transmission', filters.transmission);
    }

    if (filters.fuelSystem) {
      params = params.set('fuel_system', filters.fuelSystem);
    }

    if (filters.priceMin !== undefined || filters.priceMax !== undefined) {
      const min = filters.priceMin || '';
      const max = filters.priceMax || '';
      params = params.set('price', `${min}-${max}`);
    }

    if (filters.search) {
      params = params.set('find', filters.search);
    }

    return this.http.get(`${this.apiUrl}/${type}/`, { params });
  }
}

// Usage in component
export class VehicleListComponent implements OnInit {
  listings$ = new BehaviorSubject<any[]>([]);
  
  filters: VehicleFilters = {
    vehicleTypes: ['car', 'uav'],
    brands: ['Toyota', 'DJI']
  };

  constructor(private vehicleService: VehicleService) {}

  ngOnInit() {
    this.loadListings();
  }

  loadListings() {
    this.vehicleService.getListings('buy', this.filters)
      .subscribe(response => {
        this.listings$.next(response.data.results);
      });
  }

  onFilterChange(filters: VehicleFilters) {
    this.filters = filters;
    this.loadListings();
  }
}
```


## UI Component Examples

### Filter Dropdown Component (React)

```jsx
import React, { useState } from 'react';

const VehicleTypeFilter = ({ onChange }) => {
  const [selectedTypes, setSelectedTypes] = useState([]);

  const vehicleTypes = [
    { value: 'car', label: 'Cars', icon: '🚗' },
    { value: 'boat', label: 'Boats', icon: '⛵' },
    { value: 'plane', label: 'Planes', icon: '✈️' },
    { value: 'bike', label: 'Bikes', icon: '🏍️' },
    { value: 'uav', label: 'Drones', icon: '🚁' }
  ];

  const toggleType = (type) => {
    const newTypes = selectedTypes.includes(type)
      ? selectedTypes.filter(t => t !== type)
      : [...selectedTypes, type];
    
    setSelectedTypes(newTypes);
    onChange(newTypes);
  };

  return (
    <div className="vehicle-type-filter">
      <h3>Vehicle Type</h3>
      <div className="type-buttons">
        {vehicleTypes.map(({ value, label, icon }) => (
          <button
            key={value}
            className={`type-btn ${selectedTypes.includes(value) ? 'active' : ''}`}
            onClick={() => toggleType(value)}
          >
            <span className="icon">{icon}</span>
            <span className="label">{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default VehicleTypeFilter;
```

### CSS Styling Example

```css
.vehicle-type-filter {
  margin-bottom: 2rem;
}

.type-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 100px;
}

.type-btn:hover {
  border-color: #2196F3;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.type-btn.active {
  border-color: #2196F3;
  background: #E3F2FD;
}

.type-btn .icon {
  font-size: 2rem;
}

.type-btn .label {
  font-size: 0.875rem;
  font-weight: 500;
}
```

## Response Structure

### Listing Response Format

```json
{
  "error": false,
  "message": "",
  "data": {
    "pagination": {
      "offset": 0,
      "limit": 20,
      "count": 45,
      "next": "/api/v1/listings/buy/?vehicle_type=car&offset=20",
      "previous": null
    },
    "results": [
      {
        "uuid": "abc-123",
        "title": "2023 Toyota Camry",
        "listing_type": "sale",
        "price": 5000000,
        "vehicle": {
          "kind": "car",
          "name": "2023 Toyota Camry",
          "brand": "Toyota",
          "model": "Camry",
          "condition": "new",
          "transmission": "Automatic",
          "fuel_system": "Petrol",
          "color": "Black",
          "mileage": "0",
          "doors": 4,
          "seats": 5,
          "drivetrain": "FWD"
        }
      }
    ]
  }
}
```

### UAV-Specific Response

```json
{
  "uuid": "xyz-789",
  "title": "DJI Mavic 3 Pro",
  "listing_type": "sale",
  "price": 2500000,
  "vehicle": {
    "kind": "uav",
    "name": "DJI Mavic 3 Pro",
    "brand": "DJI",
    "model": "Mavic 3 Pro",
    "condition": "new",
    "color": "Gray",
    "uav_type": "quadcopter",
    "purpose": "photography",
    "max_flight_time": 43,
    "max_range": 30,
    "max_altitude": 6000,
    "max_speed": 75,
    "camera_resolution": "5.1K",
    "payload_capacity": 0.9,
    "weight": 0.895,
    "rotor_count": 4,
    "has_obstacle_avoidance": true,
    "has_gps": true,
    "has_return_to_home": true
  }
}
```


## Handling Vehicle Types in UI

### Dynamic Vehicle Card Component

```jsx
const VehicleCard = ({ listing }) => {
  const { vehicle } = listing;
  
  // Render different specs based on vehicle type
  const renderSpecs = () => {
    switch (vehicle.kind) {
      case 'car':
        return (
          <>
            <div className="spec">🚪 {vehicle.doors} Doors</div>
            <div className="spec">💺 {vehicle.seats} Seats</div>
            <div className="spec">⚙️ {vehicle.transmission}</div>
            <div className="spec">⛽ {vehicle.fuel_system}</div>
          </>
        );
      
      case 'uav':
        return (
          <>
            <div className="spec">🕐 {vehicle.max_flight_time} min flight</div>
            <div className="spec">📏 {vehicle.max_range} km range</div>
            <div className="spec">📷 {vehicle.camera_resolution}</div>
            <div className="spec">⚖️ {vehicle.weight} kg</div>
            {vehicle.has_obstacle_avoidance && (
              <div className="spec">🛡️ Obstacle Avoidance</div>
            )}
          </>
        );
      
      case 'plane':
        return (
          <>
            <div className="spec">✈️ {vehicle.aircraft_type}</div>
            <div className="spec">⛰️ {vehicle.max_altitude} ft altitude</div>
            <div className="spec">📏 {vehicle.wing_span} m wingspan</div>
            <div className="spec">🛫 {vehicle.range} km range</div>
          </>
        );
      
      case 'boat':
        return (
          <>
            <div className="spec">⚓ {vehicle.hull_material}</div>
            <div className="spec">🔧 {vehicle.engine_count} engines</div>
            <div className="spec">📏 {vehicle.length} ft length</div>
          </>
        );
      
      case 'bike':
        return (
          <>
            <div className="spec">🏍️ {vehicle.bike_type}</div>
            <div className="spec">⚙️ {vehicle.engine_capacity} cc</div>
            <div className="spec">⛽ {vehicle.fuel_system}</div>
          </>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="vehicle-card">
      <div className="vehicle-image">
        <img src={vehicle.images[0]?.url} alt={listing.title} />
        <span className="vehicle-type-badge">{vehicle.kind}</span>
      </div>
      <div className="vehicle-info">
        <h3>{listing.title}</h3>
        <p className="brand">{vehicle.brand} {vehicle.model}</p>
        <div className="specs">{renderSpecs()}</div>
        <div className="price">₦{listing.price.toLocaleString()}</div>
      </div>
    </div>
  );
};
```

## Best Practices

### 1. Default Filters
```javascript
// Show all vehicle types by default
const defaultFilters = {
  vehicleTypes: [], // Empty = all types
  brands: [],
  priceRange: null
};
```

### 2. URL State Management
```javascript
import { useSearchParams } from 'react-router-dom';

const VehicleListPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const vehicleTypes = searchParams.get('vehicle_type')?.split(',') || [];
  
  const updateFilters = (types) => {
    const params = new URLSearchParams(searchParams);
    if (types.length > 0) {
      params.set('vehicle_type', types.join(','));
    } else {
      params.delete('vehicle_type');
    }
    setSearchParams(params);
  };
  
  return <VehicleList vehicleTypes={vehicleTypes} onChange={updateFilters} />;
};
```

### 3. Loading States
```jsx
const VehicleList = ({ filters }) => {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (loading) {
    return (
      <div className="loading-state">
        <Spinner />
        <p>Loading vehicles...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-state">
        <p>Failed to load listings: {error}</p>
        <button onClick={retry}>Retry</button>
      </div>
    );
  }

  if (listings.length === 0) {
    return (
      <div className="empty-state">
        <p>No vehicles found matching your filters</p>
        <button onClick={clearFilters}>Clear Filters</button>
      </div>
    );
  }

  return (
    <div className="vehicle-grid">
      {listings.map(listing => (
        <VehicleCard key={listing.uuid} listing={listing} />
      ))}
    </div>
  );
};
```

### 4. Debounced Search
```javascript
import { useEffect, useState } from 'react';
import { debounce } from 'lodash';

const SearchBar = ({ onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    const debouncedSearch = debounce(() => {
      onSearch(searchTerm);
    }, 500);

    debouncedSearch();
    
    return () => debouncedSearch.cancel();
  }, [searchTerm]);

  return (
    <input
      type="text"
      placeholder="Search vehicles..."
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
    />
  );
};
```

## Common Pitfalls

### ❌ Don't do this:
```javascript
// Sending empty string instead of omitting parameter
fetch('/api/v1/listings/buy/?vehicle_type=')

// Using wrong separator
fetch('/api/v1/listings/buy/?vehicle_type=car|bike')

// Not encoding special characters
fetch(`/api/v1/listings/buy/?brands=${brands}`) // brands might have spaces
```

### ✅ Do this instead:
```javascript
// Omit parameter if empty
const params = new URLSearchParams();
if (vehicleTypes.length > 0) {
  params.append('vehicle_type', vehicleTypes.join(','));
}

// Use comma separator
params.append('vehicle_type', 'car,bike,uav');

// Properly encode parameters
const params = new URLSearchParams();
params.append('brands', brands.join(','));
fetch(`/api/v1/listings/buy/?${params}`);
```

## Testing

### Unit Test Example (Jest)

```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import VehicleTypeFilter from './VehicleTypeFilter';

describe('VehicleTypeFilter', () => {
  it('should call onChange with selected types', () => {
    const onChange = jest.fn();
    render(<VehicleTypeFilter onChange={onChange} />);
    
    fireEvent.click(screen.getByText('Cars'));
    expect(onChange).toHaveBeenCalledWith(['car']);
    
    fireEvent.click(screen.getByText('Drones'));
    expect(onChange).toHaveBeenCalledWith(['car', 'uav']);
  });

  it('should toggle types on/off', () => {
    const onChange = jest.fn();
    render(<VehicleTypeFilter onChange={onChange} />);
    
    const carButton = screen.getByText('Cars');
    fireEvent.click(carButton);
    fireEvent.click(carButton);
    
    expect(onChange).toHaveBeenLastCalledWith([]);
  });
});
```

## Support

For issues or questions:
- Backend API: See `VEHICLE_TYPE_FILTER_UPDATE.md`
- UAV Features: See `UAV_VEHICLE_TYPE_UPDATE.md`
- Migration: See `MIGRATION_COMMANDS.md`
