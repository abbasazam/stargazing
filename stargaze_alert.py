import os
import requests
from datetime import datetime
import pytz
from google import genai
import smtplib
from email.mime.text import MIMEText

# Middle Fork River Forest Preserve Coordinates (Penfield, IL - Dark Sky Park)
LAT = 40.2831
LON = -87.9714

# --- NOTIFICATION CONFIGURATION ---
SENDER_EMAIL = "abbasazam004@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# List of recipient email addresses
RECIPIENT_EMAILS = [
    "abbasazam002@gmail.com",
    # "friend1@example.com",
]

# Set to True to receive an email status update even if conditions fail.
SEND_IF_CONDITIONS_POOR = True

# TARGET DATE FOR EVENT
TARGET_DATE = "2026-09-12"


def fetch_september_12_forecast():
    """Fetches weather and lunar metrics specifically for September 12-13, 2026 via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": TARGET_DATE,
        "end_date": "2026-09-13",
        "hourly": "cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,relative_humidity_2m,wind_speed_10m,visibility,precipitation_probability",
        "daily": "moonrise,moonset,moon_phase",
        "timezone": "America/Chicago"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def evaluate_sept_12_event(forecast_json):
    """Passes September 12 forecast data to Gemini to evaluate event conditions."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    You are an expert astronomer evaluating weather conditions specifically for Saturday, September 12, 2026 at Middle Fork River Forest Preserve (Penfield, IL).
    
    EVENT SCHEDULE FOR SEPT 12, 2026:
    1. Cosmic Surfing Session: 6:00 PM – 7:30 PM CDT (Interactive outdoor session outside Interpretive Center).
    2. Guided Stargazing & Dark Sky Viewing: 8:00 PM – 11:59 PM CDT (Dark Sky Trail stargazing session).

    HOURLY WEATHER FORECAST FOR SEPT 12–13:
    {forecast_json.get('hourly', {})}

    DAILY LUNAR DATA (Sept 12):
    {forecast_json.get('daily', {})}

    EVALUATION CRITERIA FOR "ALERT: YES":
    - Stargazing Dark Hours (8:00 PM – Midnight CDT):
      * Total cloud cover MUST be <15% with zero low/mid cloud obstruction.
      * Relative humidity <80% and horizontal visibility >15 km (no heavy haze/fog).
      * Moon phase <25% or Moon set during dark hours (minimal lunar wash out).
      * Rain probability near 0%.
    - Cosmic Surfing Event (6:00 PM – 7:30 PM CDT):
      * No active rain/thunderstorms and reasonable wind (<15 mph) for comfortable outdoor standing.

    INSTRUCTIONS & OUTPUT FORMAT:
    Output "ALERT: YES" if conditions during 8:00 PM - Midnight support clear stargazing. Otherwise, output "ALERT: NO".

    Format your output strictly in two parts:
    Line 1 MUST be either "ALERT: YES" or "ALERT: NO".
    Line 2+ should be a clear summary covering:
       - Cosmic Surfing Outlook (6:00 PM - 7:30 PM CDT): Temperature, wind, and rain risk for the outdoor gathering.
       - Stargazing Outlook (8:00 PM - Midnight CDT): Cloud cover breakdown (low/mid/high), relative humidity, visibility, and wind.
       - Lunar Conditions: Moonrise/moonset times and phase percentage on Sept 12.
       - Astronomical Targets Verdict: Naked-eye visibility status for the Milky Way Core (setting in South/Southwest) and Andromeda Galaxy (M31).
       - Recommended Attire/Equipment Tips (e.g., layers, red light flashlight).
    """
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text


def send_email_alerts(subject, body, recipients):
    """Sends email alerts to recipient list via Gmail SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        print(f"Emails successfully sent to: {', '.join(recipients)}")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    print(f"Fetching specific weather forecast for {TARGET_DATE} at Middle Fork...")
    raw_forecast = fetch_september_12_forecast()
    
    print("Evaluating September 12 Cosmic Surfing & Stargazing conditions with AI...")
    analysis = evaluate_sept_12_event(raw_forecast)
    print("\n--- LLM Response ---")
    print(analysis)
    
    if "ALERT: YES" in analysis:
        print("\nGreat conditions predicted for September 12! Sending alert emails...")
        subject = "🌌 EXCELLENT SKY ALERT: September 12 Stargazing & Cosmic Surfing Event at Middle Fork!"
        send_email_alerts(subject, analysis, RECIPIENT_EMAILS)
        
    else:
        print("\nConditions for September 12 are sub-optimal.")
        if SEND_IF_CONDITIONS_POOR:
            print("Sending September 12 Status Email...")
            subject = "☁️ Sept 12 Event Update: Cloud/Weather Advisory for Middle Fork"
            
            poor_body = (
                "SEPTEMBER 12 EVENT WEATHER UPDATE:\n"
                "Current forecast indicates sub-optimal sky conditions for deep-sky viewing during the Sept 12 event.\n\n"
                "--- AI Breakdown ---\n"
                f"{analysis}"
            )
            
            send_email_alerts(subject, poor_body, RECIPIENT_EMAILS)
