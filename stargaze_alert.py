import os
import requests
from datetime import datetime
import pytz
from google import genai

# Middle Fork River Forest Preserve Coordinates (Penfield, IL)
LAT = 40.2831
LON = -87.9714

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

def send_alert_email(subject, body):
    """Sends an email alert using Python's built-in smtplib."""
    import smtplib
    from email.mime.text import MIMEText

    SENDER_EMAIL = "abbasazam004@gmail.com"  
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
    RECIPIENT_EMAIL = "abbasazam004@gmail.com" 

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())

if __name__ == "__main__":
    print("Fetching 72-hour weather and lunar data from Open-Meteo...")
    raw_forecast = fetch_72h_astronomy_forecast()
    
    print("Evaluating stargazing & deep sky quality with AI...")
    analysis = evaluate_with_llm(raw_forecast)
    print("\n--- LLM Response ---")
    print(analysis)
    
    if "ALERT: YES" in analysis:
        print("\nGood conditions detected! Sending alert...")
        send_alert_email("✨ Stargazing Alert: Middle Fork Preserve!", analysis)
    else:
        print("\nConditions are sub-optimal. No alert sent.")
