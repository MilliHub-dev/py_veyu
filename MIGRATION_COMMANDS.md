# Database Migration Commands

## After UAV Model Addition

Run these commands to create and apply the database migration for the new UAV vehicle type:

```bash
# Create migration file
python manage.py makemigrations listings

# Apply migration to database
python manage.py migrate listings

# Verify migration
python manage.py showmigrations listings
```

## Expected Migration

The migration will create a new table `listings_uav` that inherits from `listings_vehicle` with these additional columns:

- registration_number (VARCHAR)
- uav_type (VARCHAR)
- purpose (VARCHAR)
- max_flight_time (INTEGER)
- max_range (INTEGER)
- max_altitude (INTEGER)
- max_speed (INTEGER)
- camera_resolution (VARCHAR)
- payload_capacity (DECIMAL)
- weight (DECIMAL)
- rotor_count (INTEGER)
- has_obstacle_avoidance (BOOLEAN)
- has_gps (BOOLEAN)
- has_return_to_home (BOOLEAN)

## Rollback (if needed)

If you need to rollback the migration:

```bash
# Find the migration number
python manage.py showmigrations listings

# Rollback to previous migration (replace XXXX with previous migration number)
python manage.py migrate listings XXXX

# Delete the migration file
rm listings/migrations/XXXX_uav.py
```

## Testing After Migration

```bash
# Test creating a UAV via Django shell
python manage.py shell

>>> from listings.models import UAV
>>> from accounts.models import Dealership
>>> dealer = Dealership.objects.first()
>>> uav = UAV.objects.create(
...     dealer=dealer,
...     name="DJI Mavic 3",
...     brand="DJI",
...     model="Mavic 3",
...     condition="new",
...     color="Gray",
...     uav_type="quadcopter",
...     purpose="photography",
...     max_flight_time=46,
...     max_range=30,
...     camera_resolution="5.1K",
...     has_gps=True
... )
>>> print(uav)
>>> print(uav.__class__.__name__.lower())  # Should print 'uav'
```

## Verifying in Admin

1. Start development server: `python manage.py runserver`
2. Navigate to: `http://localhost:8000/admin/listings/uav/`
3. You should see the UAV admin interface with all fields organized in fieldsets

## API Testing

```bash
# Test vehicle type filter
curl "http://localhost:8000/api/v1/listings/buy/?vehicle_type=uav"

# Test with authentication (replace TOKEN)
curl -H "Authorization: Bearer TOKEN" \
     "http://localhost:8000/api/v1/listings/buy/?vehicle_type=uav,drone"
```
