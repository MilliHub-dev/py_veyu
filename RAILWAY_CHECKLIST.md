# Railway Deployment Checklist

## Pre-Deployment Checklist

### 1. Code Preparation
- [ ] All code committed and pushed to GitHub
- [ ] All dependencies listed in `requirements.txt`
- [ ] Environment variables documented
- [ ] Database migrations are up to date
- [ ] Static files configuration tested

### 2. Local Testing
- [ ] Run diagnostic script: `python debug_railway.py`
- [ ] Run deployment test: `python test_deployment.py`
- [ ] Test health endpoint locally
- [ ] Verify all Django checks pass: `python manage.py check --deploy`

### 3. Railway Project Setup
- [ ] Railway account created
- [ ] GitHub repository connected
- [ ] PostgreSQL database service added
- [ ] Redis service added (optional but recommended)

## Environment Variables Setup

### Required Variables
Copy these to Railway dashboard → Your Service → Variables:

```bash
# Core Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=veyu.railway_settings

# Database (auto-provided by Railway PostgreSQL)
DATABASE_URL=postgresql://... (automatically set)

# Media Storage
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Email Configuration
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Production Settings
DEBUG=False
```

### Optional Variables
```bash
# Caching (auto-provided by Railway Redis)
REDIS_URL=redis://... (automatically set if Redis added)

# Custom Domain
CUSTOM_DOMAIN=yourdomain.com

# Additional Services
AFRICAS_TALKING_API_KEY=your-api-key
PAYSTACK_LIVE_SECRET_KEY=your-paystack-key
```

## Deployment Steps

### 1. Initial Deployment
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically start building

### 2. Add Database
1. In project dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Wait for provisioning (DATABASE_URL will be auto-set)

### 3. Configure Environment Variables
1. Go to your service → Variables tab
2. Add all required environment variables from above
3. Save changes (this will trigger a redeploy)

### 4. Add Redis (Recommended)
1. Click "New" → "Database" → "Redis"
2. Wait for provisioning (REDIS_URL will be auto-set)

### 5. Custom Domain (Optional)
1. Go to service → Settings → Domains
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as instructed

## Post-Deployment Verification

### 1. Check Deployment Status
- [ ] Build completed successfully
- [ ] Health check passing
- [ ] No error logs in Railway dashboard

### 2. Test Endpoints
- [ ] Health check: `https://your-app.up.railway.app/health/`
- [ ] API docs: `https://your-app.up.railway.app/api/docs/`
- [ ] Admin panel: `https://your-app.up.railway.app/admin/`

### 3. Verify Functionality
- [ ] Database connections working
- [ ] Static files loading
- [ ] Media uploads working (if Cloudinary configured)
- [ ] Email sending working
- [ ] API endpoints responding correctly

## Troubleshooting Common Issues

### Build Failures
1. **Missing Dependencies**
   - Check `requirements.txt` is complete
   - Verify Python version compatibility
   - Look for version conflicts in build logs

2. **Environment Variable Issues**
   - Ensure all required variables are set
   - Check variable names for typos
   - Verify sensitive values are properly escaped

### Runtime Failures
1. **Health Check Failures**
   - Check Railway deployment logs
   - Verify database connection
   - Test health endpoint manually
   - Run diagnostic script locally

2. **Database Issues**
   - Ensure PostgreSQL service is running
   - Check DATABASE_URL is set
   - Verify migrations completed
   - Test database connection in logs

3. **Static Files Issues**
   - Check collectstatic completed successfully
   - Verify WhiteNoise configuration
   - Test static file URLs

### Performance Issues
1. **Slow Response Times**
   - Add Redis for caching
   - Monitor resource usage in Railway dashboard
   - Optimize database queries
   - Consider upgrading Railway plan

2. **Memory Issues**
   - Check memory usage in Railway dashboard
   - Optimize Django settings
   - Consider increasing worker count

## Monitoring and Maintenance

### 1. Regular Checks
- [ ] Monitor Railway dashboard for errors
- [ ] Check health endpoint regularly
- [ ] Review application logs
- [ ] Monitor resource usage

### 2. Updates and Maintenance
- [ ] Keep dependencies updated
- [ ] Monitor security advisories
- [ ] Regular database backups
- [ ] Test deployments in staging first

### 3. Scaling Considerations
- [ ] Monitor traffic patterns
- [ ] Plan for peak usage
- [ ] Consider horizontal scaling
- [ ] Optimize for Railway's infrastructure

## Emergency Procedures

### 1. Rollback Process
1. Go to Railway dashboard
2. Navigate to Deployments tab
3. Find previous working deployment
4. Click "Redeploy" on that version

### 2. Debug Process
1. Check Railway logs first
2. Test health endpoint
3. Run diagnostic script locally
4. Check environment variables
5. Verify database connectivity

### 3. Support Resources
- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- GitHub Issues: Create issue in your repository
- Health Endpoint: `/health/` for detailed status

## Success Criteria

Your deployment is successful when:
- [ ] ✅ Build completes without errors
- [ ] ✅ Health check returns 200 status
- [ ] ✅ All API endpoints respond correctly
- [ ] ✅ Database operations work
- [ ] ✅ Static files load properly
- [ ] ✅ No critical errors in logs
- [ ] ✅ Application performs well under load

## Next Steps After Successful Deployment

1. **Set up monitoring** - Configure alerts for downtime
2. **Configure backups** - Set up regular database backups
3. **Performance optimization** - Add Redis, optimize queries
4. **Security review** - Ensure all security settings are correct
5. **Documentation** - Update API documentation and user guides

---

🎉 **Congratulations!** Your Django application is now successfully deployed on Railway!