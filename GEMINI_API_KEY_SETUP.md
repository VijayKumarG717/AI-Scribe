# How to Get a Valid Gemini API Key

If you're getting an "API key not valid" error, follow these steps:

## 1. Get a Gemini API Key from Google AI Studio

1. Go to: https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the API key (it should start with "AIza...")

## 2. Update Your .env File

Open your `.env` file in the project directory and update it:

```
GEMINI_API_KEY=your_new_api_key_here
ASSEMBLYAI_API_KEY=29c2b594dcaf4c18ba93348005a9bc22
```

**Important Notes:**
- The API key should start with "AIza"
- Don't add quotes around the API key
- No spaces before or after the = sign
- Make sure there are no extra characters

Example:
```
GEMINI_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567
```

## 3. Restart the Flask App

After updating the .env file, restart your Flask app to load the new API key.

## Troubleshooting

- If the key still doesn't work, verify it's active in Google AI Studio
- Check that the API key has access to the Generative Language API
- Make sure there are no quote marks or extra spaces in the .env file

