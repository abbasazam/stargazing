import os
import requests
from datetime import datetime
import pytz
from google import genai
import smtplib
from email.mime.text import MIMEText

# Middle Fork River Forest Preserve Coordinates (Penfield, IL)
LAT = 40.2831
LON = -87.9714

# --- NOTIFICATION CONFIGURATION ---
SENDER_EMAIL = "abbasazam004@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Add all recipient emails to this list
RECIPIENT_EMAILS = [
    "abbasazam002@gmail.com",
    # "khadijaazam400@gmail.com",
    # "chaudhrynabila4@gmail.com",
]

# Set to True if you want an email even when conditions are BAD.
# Set to False to only receive emails when conditions are GOOD.
SEND_IF_CONDITIONS_POOR = True


def fetch_72h_astronomy_forecast():
    """Fetches key stargazing weather and lunar metrics for the next 72 hours via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,relativehumidity_2m,windspeed_10m,visibility",
        "daily": "moonrise,moonset,moon_phase",
        "forecast_hours": 72,
        "timezone": "America/Chicago"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def evaluate_with_llm(forecast_json):
    """Passes the raw 72-hour forecast and lunar data to Gemini to evaluate stargazing conditions."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    chicago_tz = pytz.timezone("America/Chicago")
    now_str = datetime.now(chicago_tz).strftime("%Y-%m-%d %I:%M %p %Z")
    
    prompt = f"""
    You are an expert astronomer assistant evaluating night sky viewing conditions.
    CURRENT TIME RIGHT NOW: {now_str}
    
    HOURLY WEATHER FORECAST (Next 72 Hours):
    {forecast_json['hourly']}

    DAILY LUNAR DATA (Moonrise, Moonset, Moon Phase):
    {forecast_json.get('daily', {})}

    INSTRUCTIONS:
    1. Look STRICTLY at UPCOMING night hours (roughly 9 PM to 4 AM CDT) over the next 72 hours starting AFTER {now_str}.
    2. Evaluate BOTH weather and lunar interference:
       - Weather: Cloud cover <20%, low humidity (good transparency), low wind (<10 mph).
       - Moonlight/Galactic Visibility: Evaluate if bright moonlight will wash out deep-sky objects like the Milky Way core or faint nebulae. 
         * Ideal: Moon phase near New Moon OR Moon has set during the dark night hours.
         * Compromised: Bright Moon (>50% illumination) high in the sky during midnight hours.
    3. Determine if there is a prime viewing window coming up within 72 hours.
    4. Format your output strictly in two parts:
       Line 1 MUST be either "ALERT: YES" or "ALERT: NO".
       Line 2+ should be a clear summary explaining:
         - Weather conditions (clouds, wind, transparency)
         - Lunar conditions (moon phase & whether the moon is below the horizon during dark hours)
         - Overall impact on Deep Sky / Milky Way visibility vs planetary viewing.
    """
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text


def send_email_alerts(subject, body, recipients):
    """Sends email alerts to a list of recipient email addresses via Gmail SMTP."""
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
    print("Fetching 72-hour weather and lunar data from Open-Meteo...")
    raw_forecast = fetch_72h_astronomy_forecast()
    
    print("Evaluating stargazing & deep sky quality with AI...")
    analysis = evaluate_with_llm(raw_forecast)
    print("\n--- LLM Response ---")
    print(analysis)
    
    if "ALERT: YES" in analysis:
        print("\nGood conditions detected! Sending alert emails...")
        subject = "✨ Stargazing Alert: Prime Sky Conditions Ahead at Middle Fork!"
        send_email_alerts(subject, analysis, RECIPIENT_EMAILS)
        
    else:
        print("\nConditions are sub-optimal.")
        if SEND_IF_CONDITIONS_POOR:
            print("Sending 'Poor Conditions' status update email...")
            
            # --- ONE-LINER OPTIONS FOR POOR CONDITIONS ---
            # You can pick any of these one-liners for the subject line:
            # Option A: "☁️ Stargazing Update: Poor conditions expected over the next 72 hours."
            # Option B: "🚫 No Stargazing Alert: High clouds and moon washouts ahead."
            # Option C: "🔭 Stargazing Update: Sub-optimal skies – save your trip for another night."
            
            subject = "☁️ Stargazing Update: Poor conditions expected over the next 72 hours."
            
            poor_body = (
                "NO ALERT: Stargazing conditions over the next 72 hours are sub-optimal "
                "due to high cloud cover, excessive humidity, or heavy lunar interference.\n\n"
                "--- Detailed AI Breakdown ---\n"
                f"{analysis}"
            )
            
            send_email_alerts(subject, poor_body, RECIPIENT_EMAILS)
