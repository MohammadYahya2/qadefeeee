# Telegram Integration Setup Guide

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a conversation with BotFather by clicking **Start**
3. Send the command `/newbot`
4. Follow the prompts:
   - Choose a name for your bot (e.g., "Shoes Store Bot")
   - Choose a username ending with "bot" (e.g., "shoes_store_orders_bot")
5. BotFather will give you a **Bot Token** - save this! It looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

## Step 2: Create a Telegram Channel (Optional but Recommended)

1. Create a new Telegram channel:
   - Click the **New Message** button in Telegram
   - Select **New Channel**
   - Name your channel (e.g., "Shoes Store Orders")
   - Set it as **Private** for security
2. Add your bot as an administrator:
   - Go to your channel settings
   - Click **Administrators**
   - Click **Add Administrator**
   - Search for your bot's username
   - Give it permission to **Post Messages**

## Step 3: Get Your Chat ID

### For a Channel:
1. Forward any message from your channel to **@RawDataBot**
2. Look for `"chat":{"id":-1001234567890}` in the response
3. Your Chat ID is the number (including the minus sign): `-1001234567890`

### For a Private Chat with the Bot:
1. Send any message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. Your Chat ID is the number: `123456789`

## Step 4: Update Django Settings

Replace the placeholder values in `shoes/settings.py`:

```python
# Telegram integration settings (replaces WhatsApp)
TELEGRAM_BOT_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'  # Your actual Bot Token
TELEGRAM_CHAT_ID = '-1001234567890'  # Your channel or chat ID
```

## Step 5: Install Dependencies

Run the following command to install required packages:

```bash
pip install -r requirements.txt
```

## Step 6: Test the Integration

1. Start the Django server: `python manage.py runserver`
2. Place a test order through the website
3. Check your Telegram channel/chat for the order notification with product images

## Important Notes

- **Channel vs Private Chat**: Channels are recommended for business use as they provide better organization
- **Bot Permissions**: Make sure your bot has permission to send messages and photos
- **Message Formatting**: The bot sends messages with HTML formatting for better readability
- **Image Handling**: Product images are sent as separate photos with captions

## Message Format

The bot will send order notifications containing:
- 📋 **Order Details**: Order ID, customer info, address
- 🛍️ **Product Information**: Name, color, size, quantity, price
- 💳 **Total Amount**: Final price calculation
- 📸 **Product Photos**: Individual images with product details

## Troubleshooting

### Bot Not Sending Messages
- Verify your Bot Token is correct
- Check that the Chat ID is accurate (include minus sign for channels)
- Ensure the bot is added as administrator to your channel

### Images Not Sending
- Check that product images exist in the media directory
- Verify MEDIA_ROOT and SITE_URL settings are correct
- Ensure the bot has permission to send photos

### Permission Issues
- Make sure the bot is administrator of your channel
- Check that "Post Messages" permission is enabled for the bot

## Testing Without Real Setup

If you haven't set up Telegram yet, the system will log messages to the Django console for testing purposes. You'll see the message content and image URLs in the server logs.

## Security Considerations

- Keep your Bot Token secret - don't commit it to version control
- Use environment variables for production deployment
- Consider using a private channel for order notifications
- Regularly review bot administrators and permissions

## Production Deployment

For production, consider:
1. Using environment variables for sensitive data:
   ```python
   import os
   TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
   TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
   ```
2. Setting up webhook instead of polling for better performance
3. Implementing message rate limiting if needed
4. Adding error monitoring for notification failures 