# Railway Deployment Guide

## Quick Setup

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `py_veyu` repository
   - Railway will automatically detect it's a Django app

3. **Add PostgreSQL Database**
   - In your project dashboard, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

4. **Configure Environment Variables**
   Go to your service → Variables tab and add:

   ```
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_SETTINGS_MODULE=veyu.railway_settings
   CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
   EMAIL_HOST_USER=your-email@example.com
   EMAIL_HOST_PASSWORD=your-email-password
   DEBUG=False
   ```

5. **Optional: Add Redis**
   - Click "New" → "Database" → "Redis"
   - Railway will automatically set `REDIS_URL`

## Environment Variables Explained

### Required
- `DJANGO_SECRET_KEY`: Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `DATABASE_URL`: Automatically provided by Railway PostgreSQL
- `CLOUDINARY_URL`: For media file storage (get from cloudinary.com)

### Optional
- `REDIS_URL`: Automatically provided if you add Redis database
- `DEBUG`: Set to `True` for development, `False` for production
- `CUSTOM_DOMAIN`: Your custom domain if you have one
- `EMAIL_HOST_USER`: SMTP email username
- `EMAIL_HOST_PASSWORD`: SMTP email password

## Deployment Process

Railway will automatically:
1. Install dependencies from `requirements.txt`
2. Run database migrations
3. Collect static files
4. Start the Gunicorn server

## Custom Domain (Optional)

1. Go to your service → Settings → Domains
2. Click "Custom Domain"
3. Add your domain (e.g., `api.yourdomain.com`)
4. Update your DNS to point to Railway's provided CNAME

## Monitoring

- **Logs**: View real-time logs in Railway dashboard
- **Metrics**: Monitor CPU, memory, and network usage
- **Health Check**: Railway will ping `/health/` to ensure your app is running

## Local Development

To test Railway settings locally:

```bash
# Set environment variables
export DJANGO_SETTINGS_MODULE=veyu.railway_settings
export DATABASE_URL=postgresql://user:pass@localhost/dbname
export DJANGO_SECRET_KEY=your-secret-key

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

## Troubleshooting

## Troubleshooting

### Health Check Failures

If you're getting "service unavailable" errors during health checks:

1. **Check Railway Logs**
   - Go to your Railway project dashboard
   - Click on your service
   - Go to "Deployments" tab
   - Click on the latest deployment to view logs

2. **Common Issues and Solutions**

   **Missing Environment Variables:**
   ```bash
   # Required variables in Railway dashboard:
   DJANGO_SECRET_KEY=your-secret-key-here
   DJANGO_SETTINGS_MODULE=veyu.railway_settings
   DATABASE_URL=postgresql://... (auto-provided by Railway)
   ```

   **Database Connection Issues:**
   - Ensure PostgreSQL service is running in Railway
   - Check that DATABASE_URL is automatically set
   - Verify database migrations completed successfully

   **Django Import Errors:**
   - Check that all dependencies are in requirements.txt
   - Verify Python version compatibility
   - Look for missing packages in build logs

3. **Debug Commands**
   
   Run the diagnostic script locally to test your configuration:
   ```bash
   python debug_railway.py
   ```

4. **Manual Health Check Test**
   
   Once deployed, test the health endpoint:
   ```bash
   curl https://your-app.up.railway.app/health/
   ```

### Build Failures

1. **Dependency Issues**
   - Ensure all packages are in `requirements.txt`
   - Check for version conflicts
   - Verify Python version compatibility

2. **Static Files Issues**
   - Check that `collectstatic` runs successfully
   - Verify WhiteNoise configuration
   - Ensure STATIC_ROOT is properly set

### Runtime Errors

1. **500 Internal Server Error**
   - Check Railway logs for detailed error messages
   - Verify all environment variables are set
   - Test database connectivity
   - Check Django settings configuration

2. **Database Migration Errors**
   - Check if migrations are consistent
   - Verify database permissions
   - Look for migration dependency issues

### Performance Issues

1. **Slow Response Times**
   - Add Redis for caching
   - Optimize database queries
   - Check resource usage in Railway dashboard

2. **Memory Issues**
   - Monitor memory usage in Railway dashboard
   - Optimize Django settings for production
   - Consider upgrading Railway plan if needed

### Getting Help

- **Railway Logs**: Always check deployment logs first
- **Health Endpoint**: Visit `/health/` to see detailed status
- **Debug Script**: Run `python debug_railway.py` locally
- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway

## Production Checklist

- [ ] PostgreSQL database added
- [ ] All environment variables configured
- [ ] Custom domain configured (if needed)
- [ ] Redis added for caching (recommended)
- [ ] Cloudinary configured for media files
- [ ] Email settings configured
- [ ] Health check endpoint working (`/health/`)
- [ ] API documentation accessible (`/api/docs/`)

## Performance Tips

1. **Add Redis** for caching and sessions
2. **Use Cloudinary** for media file storage
3. **Enable compression** (already configured with WhiteNoise)
4. **Monitor resource usage** in Railway dashboard
5. **Set up proper logging** (already configured)

Your Django application is now ready for Railway deployment! 🚀