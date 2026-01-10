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

### Common Issues

1. **Build Fails**
   - Check that all dependencies are in `requirements.txt`
   - Ensure `DJANGO_SECRET_KEY` is set

2. **Database Connection Error**
   - Verify PostgreSQL service is running
   - Check `DATABASE_URL` is set correctly

3. **Static Files Not Loading**
   - Ensure `python manage.py collectstatic` runs successfully
   - Check WhiteNoise is configured correctly

4. **500 Errors**
   - Check logs in Railway dashboard
   - Verify all environment variables are set
   - Test health check endpoint: `/health/`

### Getting Help

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check logs in Railway dashboard for detailed error messages

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