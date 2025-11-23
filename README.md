# 🎧 Analysis of Musical Preferences Over Time

An end-to-end data pipeline that collects Spotify listening data, stores it in AWS, and generates insights about how musical preferences evolve over time.

## Initial Setup:

1. Configure the Spotify App:
* In the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
* Add http://127.0.0.1:8000/callback
* Note down the **Client ID** and **Client Secret**.

2. Run the Terraform:
```
cd infrastructure
terraform inits
terraform apply -var="spotify_client_id=YOUR_CLIENT_ID" -var="spotify_client_secret=YOUR_CLIENT_SECRET"
```

3. Run the Setup Script:
```
python scripts/spotify_auth_setup.py
```