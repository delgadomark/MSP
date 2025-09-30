# Microsoft Business Account Setup Guide for bids@bluelinetech.org

## Overview
This guide will help you configure the `bids@bluelinetech.org` Microsoft business account for use with your Django bid sheet application.

## Step 1: Microsoft 365 Business Account Setup

### If you don't have the account yet:
1. Go to [Microsoft 365 Business](https://www.microsoft.com/microsoft-365/business)
2. Choose a business plan (Business Basic, Standard, or Premium)
3. Set up your domain `bluelinetech.org`
4. Create the `bids@bluelinetech.org` email account

### If you already have the account:
1. Sign in to [Microsoft 365 Admin Center](https://admin.microsoft.com)
2. Go to **Users** > **Active users**
3. Verify `bids@bluelinetech.org` exists or create it

## Step 2: Enable Modern Authentication & App Passwords

### For Microsoft 365 Business:
1. Sign in to [Microsoft 365 Admin Center](https://admin.microsoft.com)
2. Go to **Settings** > **Org settings** > **Security & privacy**
3. Select **Modern authentication**
4. Ensure "Enable modern authentication for Outlook" is checked

### Create App Password:
1. Sign in to [My Account](https://myaccount.microsoft.com)
2. Go to **Security** > **Additional security verification**
3. Click **App passwords**
4. Click **Create** and name it "Django Bid System"
5. Copy the generated password (you'll need this for Django)

## Step 3: Configure Django Application

### Update .env file:
The `.env` file has been created with the following configuration:
```bash
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=bids@bluelinetech.org
EMAIL_HOST_PASSWORD=your-app-password-here
DEFAULT_FROM_EMAIL=bids@bluelinetech.org
```

### Replace the app password:
1. Open `/workspaces/simple-django/.env`
2. Replace `your-app-password-here` with the app password from Step 2
3. Save the file

## Step 4: Update Django Settings

Your Django settings are already configured to use environment variables:
- `EMAIL_HOST_USER` will use `bids@bluelinetech.org`
- `DEFAULT_FROM_EMAIL` will use `bids@bluelinetech.org`
- All outgoing emails will appear to come from this address

## Step 5: Test Email Configuration

### Test from Django shell:
```python
cd /workspaces/simple-django/main
python manage.py shell

# In the shell:
from django.core.mail import send_mail
send_mail(
    'Test Email from Blue Line Technology',
    'This is a test email from the bid system.',
    'bids@bluelinetech.org',
    ['your-test-email@example.com'],
    fail_silently=False,
)
```

### Test from bid sheet system:
1. Create a bid sheet
2. Add customer email
3. Generate and send PDF via email
4. Check that email appears from `bids@bluelinetech.org`

## Step 6: Domain Configuration (Optional but Recommended)

### SPF Record:
Add to your DNS:
```
v=spf1 include:spf.protection.outlook.com -all
```

### DKIM and DMARC:
Follow Microsoft's guidance for setting up DKIM and DMARC records for better email deliverability.

## Troubleshooting

### Common Issues:
1. **Authentication errors**: Ensure you're using an app password, not your regular password
2. **SSL/TLS errors**: Verify TLS is enabled (port 587 with STARTTLS)
3. **Blocked emails**: Check Microsoft 365 mail flow rules

### Error Messages:
- "Authentication failed": Wrong app password or username
- "Connection refused": Check EMAIL_HOST and EMAIL_PORT
- "TLS error": Verify EMAIL_USE_TLS=True

## Security Notes

1. **Never commit passwords**: The `.env` file is in `.gitignore`
2. **App passwords**: More secure than regular passwords for SMTP
3. **Environment variables**: Keep sensitive data in environment variables
4. **Regular rotation**: Consider rotating app passwords periodically

## Features This Enables

With `bids@bluelinetech.org` configured, your application can:
- Send bid sheet PDFs directly to customers
- Send password reset emails
- Send system notifications
- Maintain professional branding with your domain

## Next Steps

1. Set up the Microsoft business account
2. Generate app password
3. Update the `.env` file with the real app password
4. Test email functionality
5. Consider setting up email templates with your company branding

For any issues, refer to Microsoft's SMTP documentation or Django's email documentation.
