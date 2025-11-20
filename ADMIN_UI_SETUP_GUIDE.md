# GidiNest Admin UI - Setup Guide

## Overview

The GidiNest admin interface has been upgraded with a professional, modern, and user-friendly design using **django-jazzmin**. This guide will help you install and configure the new admin UI.

---

## Features

### ✨ Modern Design
- **Professional Theme**: Clean, modern interface with gradient accents
- **Responsive Layout**: Works seamlessly on desktop, tablet, and mobile
- **Custom Branding**: GidiNest branding with purple/blue gradient theme
- **Dark Sidebar**: Professional dark sidebar with colored icons

### 📊 Enhanced Dashboard
- **Custom Homepage**: Welcome banner with quick stats and action buttons
- **Support Dashboard**: Comprehensive metrics and real-time monitoring
- **Icon-Enhanced Cards**: FontAwesome icons for better visual hierarchy
- **Animated Elements**: Smooth transitions and hover effects

### 🎨 Improved UI Components
- **Better Tables**: Enhanced table styling with hover effects
- **Modern Forms**: Improved form fields with better focus states
- **Custom Badges**: Color-coded status badges
- **Professional Buttons**: Gradient buttons with hover animations

### 🔧 User-Friendly Features
- **Quick Search**: Global search for users and customer notes
- **Top Menu Links**: Quick access to support dashboard and key sections
- **Custom Icons**: FontAwesome icons for all models and apps
- **Organized Sidebar**: Logical ordering of apps and models

---

## Installation Steps

### Step 1: Install django-jazzmin

The package has already been added to `requirements.txt`. Install it by running:

```bash
pip install -r requirements.txt
```

Or install it directly:

```bash
pip install django-jazzmin==3.0.1
```

### Step 2: Verify Configuration

The following changes have already been made to your project:

#### ✅ `gidinest_backend/settings.py`
- Added `'jazzmin'` to `INSTALLED_APPS` (must be before `django.contrib.admin`)
- Added comprehensive `JAZZMIN_SETTINGS` configuration
- Added `JAZZMIN_UI_TWEAKS` for theme customization

#### ✅ `templates/admin/index.html`
- Custom admin homepage with welcome banner
- Quick stats cards with placeholders
- Quick action buttons for common tasks

#### ✅ `templates/admin/support_dashboard.html`
- Enhanced support dashboard with modern styling
- Icon-enhanced metric cards
- Professional gradient header

#### ✅ `static/admin/css/custom_admin.css`
- Custom CSS for enhanced styling
- Improved typography with Inter font
- Better form controls and table styling
- Smooth animations and transitions

### Step 3: Collect Static Files

After installation, collect static files:

```bash
python manage.py collectstatic --noinput
```

### Step 4: Restart the Server

Restart your Django development server:

```bash
python manage.py runserver
```

Or if you're using Gunicorn in production:

```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## Accessing the Admin

### Development
```
http://localhost:8000/internal-admin/
```

### Production
```
https://api.gidinest.com/internal-admin/
```

### Support Dashboard
```
/internal-admin/support-dashboard/
```

---

## Customization Options

### Changing Colors

Edit `gidinest_backend/settings.py` and modify `JAZZMIN_UI_TWEAKS`:

```python
JAZZMIN_UI_TWEAKS = {
    "brand_colour": "navbar-success",  # Change to navbar-primary, navbar-info, etc.
    "sidebar": "sidebar-dark-success",  # Change sidebar color
    "theme": "flatly",  # Change theme (see available themes below)
}
```

### Available Themes
- default
- cerulean
- cosmo
- cyborg (dark theme)
- darkly (dark theme)
- flatly (current)
- journal
- litera
- lumen
- lux
- materia
- minty
- pulse
- sandstone
- simplex
- sketchy
- slate (dark theme)
- solar (dark theme)
- spacelab
- superhero (dark theme)
- united
- yeti

### Adding a Logo

1. Add your logo to `static/admin/images/logo.png`
2. Update `settings.py`:

```python
JAZZMIN_SETTINGS = {
    "site_logo": "admin/images/logo.png",
    "login_logo": "admin/images/logo.png",
}
```

3. Collect static files: `python manage.py collectstatic`

### Customizing Icons

Edit the `icons` dictionary in `JAZZMIN_SETTINGS` in `settings.py`:

```python
"icons": {
    "account.UserModel": "fas fa-user-circle",  # Change icon
    "wallet.Wallet": "fas fa-wallet",
    # Add more...
}
```

Browse FontAwesome icons at: https://fontawesome.com/icons

---

## Features Breakdown

### 1. Enhanced Admin Index
- **Welcome Banner**: Personalized greeting with user role
- **Quick Stats**: Placeholder cards for key metrics
- **Quick Actions**: Direct links to common admin tasks
- **Modern Design**: Gradient header with smooth animations

### 2. Support Dashboard
Located at `/internal-admin/support-dashboard/`

**Metrics Displayed:**
- 👥 User Metrics (Total, Verified, Unverified, Active)
- 💰 Wallet & Transactions (Wallets, Balance, Transactions, Withdrawals)
- 📞 Support Metrics (Open Notes, In Progress, Urgent, Resolved)
- 🏥 System Health (Sessions, Savings Goals, Errors)

**Recent Activity Sections:**
- Recent Customer Notes
- Users Awaiting Verification
- Recent Failed Withdrawals

**Quick Links:**
- Manage Users
- Customer Notes
- Withdrawals
- Transactions
- Sessions
- Server Logs

### 3. Custom CSS Enhancements
Located at `static/admin/css/custom_admin.css`

**Improvements:**
- Inter font for better typography
- Enhanced button styles with hover effects
- Professional card designs
- Improved table styling
- Better form controls
- Smooth animations
- Custom scrollbar
- Responsive design

### 4. Model Admin Icons

All models have been assigned appropriate FontAwesome icons:

| Model | Icon |
|-------|------|
| Users | fa-users |
| User Sessions | fa-laptop |
| Bank Accounts | fa-university |
| Customer Notes | fa-sticky-note |
| Audit Logs | fa-history |
| Wallets | fa-wallet |
| Transactions | fa-exchange-alt |
| Withdrawals | fa-money-bill-wave |
| Savings Goals | fa-bullseye |
| Communities | fa-users |
| Notifications | fa-bell |
| Server Logs | fa-server |

---

## Troubleshooting

### Static Files Not Loading

1. Check `STATIC_ROOT` in `settings.py`:
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

2. Run collectstatic:
```bash
python manage.py collectstatic --clear --noinput
```

3. Check Nginx configuration (production):
```nginx
location /static/ {
    alias /path/to/your/staticfiles/;
}
```

### Jazzmin Not Appearing

1. Verify `jazzmin` is in `INSTALLED_APPS` BEFORE `django.contrib.admin`
2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Check for console errors in browser developer tools

### Custom CSS Not Applying

1. Verify file exists: `static/admin/css/custom_admin.css`
2. Run collectstatic: `python manage.py collectstatic`
3. Clear browser cache
4. Check `JAZZMIN_SETTINGS["custom_css"]` points to correct path

### Icons Not Showing

1. Verify internet connection (FontAwesome loads from CDN)
2. Check `use_google_fonts_cdn` is `True` in settings
3. Clear browser cache

---

## Production Deployment

### Checklist

- [ ] Install django-jazzmin: `pip install django-jazzmin==3.0.1`
- [ ] Update requirements.txt in production
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Restart Gunicorn: `sudo systemctl restart gunicorn`
- [ ] Restart Nginx: `sudo systemctl restart nginx`
- [ ] Clear browser cache
- [ ] Test admin access
- [ ] Test support dashboard

### Nginx Configuration

Ensure your Nginx config serves static files correctly:

```nginx
location /static/ {
    alias /home/username/GidiNest-backend/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### Performance Tips

1. **Enable caching** for static files (add expires headers)
2. **Compress CSS/JS** in production
3. **Use CDN** for static assets if possible
4. **Enable gzip** in Nginx for faster loading

---

## Additional Resources

- **Jazzmin Documentation**: https://django-jazzmin.readthedocs.io/
- **FontAwesome Icons**: https://fontawesome.com/icons
- **Django Admin Documentation**: https://docs.djangoproject.com/en/stable/ref/contrib/admin/

---

## Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review Django logs: `/var/log/gunicorn/error.log`
3. Check browser console for JavaScript errors
4. Verify all static files are collected properly

---

## What's Next?

### Recommended Enhancements

1. **Add Real-Time Stats**: Connect dashboard cards to actual data via AJAX
2. **Add Charts**: Integrate Chart.js for visual analytics
3. **Add Notifications**: Real-time admin notifications for urgent issues
4. **Add Exports**: CSV/Excel export functionality for reports
5. **Add User Activity Timeline**: Visual timeline of user actions

### Future Customizations

- Add company logo to branding
- Customize color scheme to match brand
- Add custom admin actions with modal dialogs
- Implement inline editing for tables
- Add bulk operations interface

---

## Summary

Your GidiNest admin interface now features:

✅ Modern, professional design
✅ Enhanced user experience
✅ Comprehensive support dashboard
✅ Custom branding and styling
✅ Responsive layout
✅ Icon-enhanced navigation
✅ Smooth animations and transitions
✅ Better accessibility

The admin is now ready for production use! 🚀
