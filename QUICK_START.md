# Quick Start - GidiNest Admin UI

## Installation (3 Steps)

### Step 1: Install Package
```bash
pip install -r requirements.txt
```

### Step 2: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 3: Restart Server
```bash
# Development
python manage.py runserver

# Production
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## Access

### Admin Dashboard
```
Development: http://localhost:8000/internal-admin/
Production:  https://api.gidinest.com/internal-admin/
```

### Support Dashboard
```
/internal-admin/support-dashboard/
```

---

## What Changed?

| Before | After |
|--------|-------|
| Basic Django admin | Modern Jazzmin theme |
| No branding | Custom GidiNest branding |
| No icons | FontAwesome icons throughout |
| Plain dashboard | Enhanced support dashboard |
| Basic forms/tables | Professional styled components |

---

## Key Features

✅ Modern purple/blue gradient theme
✅ Dark sidebar with colored icons
✅ Enhanced support dashboard with metrics
✅ Quick search for users and notes
✅ Custom CSS with animations
✅ Responsive design (mobile-friendly)
✅ Professional typography (Inter font)

---

## Files Added/Modified

### Added
- ✅ `templates/admin/index.html` - Custom homepage
- ✅ `static/admin/css/custom_admin.css` - Custom styles
- ✅ `ADMIN_UI_SETUP_GUIDE.md` - Full setup guide
- ✅ `ADMIN_UI_UPGRADE_SUMMARY.md` - Upgrade summary

### Modified
- ✅ `requirements.txt` - Added django-jazzmin
- ✅ `gidinest_backend/settings.py` - Added Jazzmin config
- ✅ `account/admin.py` - Fixed AdminAuditLog error
- ✅ `templates/admin/support_dashboard.html` - Enhanced styling

---

## Troubleshooting

**Not seeing changes?**
```bash
python manage.py collectstatic --clear --noinput
# Then clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
```

**Icons missing?**
- Check internet connection (FontAwesome uses CDN)

**Static files not loading?**
```bash
# Check STATIC_ROOT in settings.py
python manage.py collectstatic --noinput
```

---

## Customization

### Change Theme
Edit `gidinest_backend/settings.py`:
```python
JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",  # Change to: darkly, cyborg, lux, etc.
}
```

### Change Colors
```python
JAZZMIN_UI_TWEAKS = {
    "brand_colour": "navbar-primary",  # or navbar-info, navbar-warning
    "sidebar": "sidebar-dark-primary",
}
```

### Add Logo
1. Add logo to `static/admin/images/logo.png`
2. Update settings:
```python
JAZZMIN_SETTINGS = {
    "site_logo": "admin/images/logo.png",
}
```
3. Run `python manage.py collectstatic`

---

## Documentation

- **Full Setup Guide**: `ADMIN_UI_SETUP_GUIDE.md`
- **Upgrade Summary**: `ADMIN_UI_UPGRADE_SUMMARY.md`
- **Jazzmin Docs**: https://django-jazzmin.readthedocs.io/

---

## Support

Having issues? Check:
1. Troubleshooting section in `ADMIN_UI_SETUP_GUIDE.md`
2. Django logs: `/var/log/gunicorn/error.log`
3. Browser console (F12) for JavaScript errors
4. Verify static files collected: `ls staticfiles/`

---

**That's it! Your admin is ready to use! 🎉**
