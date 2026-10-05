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
    "chaudhrynabila4@gmail.com",
    "kazam8513@stu.d214.org",
    "khadijaschool1234@gmail.com",
    "khadijaazam400@gmail.com",
]

# Set to True to receive status emails even if upcoming conditions do NOT exceed Sept 4 standards.
SEND_IF_CONDITIONS_POOR = True


def fetch_72h_astronomy_forecast():
    """Fetches weather and lunar metrics for the next 72 hours via Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,relative_humidity_2m,wind_speed_10m,visibility,precipitation_probability",
        "daily": "moonrise,moonset,moon_phase",
        "forecast_hours": 72,
        "timezone": "America/Chicago"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def evaluate_against_sept4_baseline(forecast_json):
    """Compares the upcoming 72-hour forecast against the historic Sept 4, 2026 baseline conditions."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    chicago_tz = pytz.timezone("America/Chicago")
    now = datetime.now(chicago_tz)
    now_str = now.strftime("%Y-%m-%d %I:%M %p %Z")
    current_month = now.strftime("%B")
    
    prompt = f"""
    You are an expert astronomer evaluating night sky viewing conditions at Middle Fork River Forest Preserve (Latitude ~40.3° N, Bortle 3 Dark Sky Park).
    CURRENT EXECUTION TIME: {now_str} (Current Month: {current_month})

    HISTORIC BASELINE BENCHMARK (SEPTEMBER 4, 2026 VISIT):
    The user visited the preserve on September 4, 2026 (9:00 PM – 11:45 PM CDT).
    Sept 4 Baseline Conditions:
    - Cloud Cover: Clear / ~0% total cloud cover.
    - Humidity: 82% – 86% (Moderate-to-high atmospheric moisture/haze, dew formation).
    - Wind: Light (4 mph).
    - Perceived Sky Quality: Good cloudless sky, but limited transparency due to high surface/atmospheric humidity.

    UPCOMING 72-HOUR FORECAST DATA:
    Hourly Data: {forecast_json.get('hourly', {})}
    Daily Lunar Data: {forecast_json.get('daily', {})}

    EVALUATION BENCHMARK FOR "ALERT: YES":
    The user wants to go ONLY if conditions are SIGNIFICANTLY BETTER than September 4.
    
    Criteria for "ALERT: YES":
    1. Cloud Cover: MUST be pristine (<5% cloud cover, zero low/mid clouds) during dark night hours (9:00 PM – 4:00 AM CDT).
    2. Atmospheric Transparency (CRITICAL DIFFERENCE):
       - Humidity MUST be lower than Sept 4 (<70% relative humidity, ideally <60%) to prevent ground haze and damp air scattering light.
       - Horizontal Visibility MUST be >20,000 meters (>20 km).
    3. Moonlight Interference:
       - The Moon MUST be either set during dark hours OR near New Moon (<15% illuminated). Bright moon wash-out makes conditions worse than Sept 4.
    4. Target Seasonality Check ({current_month}):
       - At least one primary target (Milky Way Core, Andromeda Galaxy M31, or Orion Nebula M42) must be well-positioned above the horizon.

    Criteria for "ALERT: NO":
    - If total cloud cover is >= 10%.
    - If humidity is >= 75% (equal to or worse atmospheric haze than Sept 4).
    - If Moon illumination > 20% is present in the sky during dark hours.
    - If overall sky viewing quality is merely equal to or worse than September 4.

    INSTRUCTIONS & OUTPUT FORMAT:
    Output "ALERT: YES" ONLY if an upcoming night window in the next 72 hours is strictly superior to the September 4 benchmark. Otherwise, output "ALERT: NO".

    Format your output strictly as follows:
    Line 1 MUST be either "ALERT: YES" or "ALERT: NO".
    
    Line 2+: Provide a clear breakdown covering:
       - Superiority Verdict: Explicitly state whether upcoming conditions beat Sept 4 and why.
       - Best Viewing Window: Date and exact hours (e.g., "Monday Sept 14, 10:00 PM – 2:00 AM CDT").
       - Direct Comparison vs Sept 4:
         * Cloud Cover: Upcoming % vs Sept 4 (~0%).
         * Transparency & Humidity: Upcoming % vs Sept 4 (82-86%). Highlight if air is drier/clearer.
         * Effective Bortle Class: Baseline Bortle 3 vs Expected Effective Bortle Class for the night.
         * Lunar Phase & Timing: Moon illumination % and horizon status.
       - Deep-Sky Object Status: Visibility of Milky Way Core, Andromeda (M31), and major nebulae.
       - Detailed Reasoning: Exhaustive breakdown of why this alert (YES or NO) was triggered.
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
    print("Fetching 72-hour weather and lunar forecast from Open-Meteo...")
    raw_forecast = fetch_72h_astronomy_forecast()
    
    print("Comparing upcoming forecast against September 4 baseline via AI...")
    analysis = evaluate_against_sept4_baseline(raw_forecast)
    print("\n--- LLM Response ---")
    print(analysis)
    
    if "ALERT: YES" in analysis:
        print("\nSuperior conditions detected (Better than Sept 4)! Sending alert emails...")
        subject = "🌟 PRISTINE SKY ALERT: Exceptional Stargazing Window (Beats Sept 4 Baseline)!"
        send_email_alerts(subject, analysis, RECIPIENT_EMAILS)
        
    else:
        print("\nConditions do not exceed the September 4 quality threshold.")
        if SEND_IF_CONDITIONS_POOR:
            print("Sending 'Sub-Optimal vs Sept 4' status email...")
            subject = "☁️ Stargazing Update: Upcoming 72h Does Not Exceed Sept 4 Quality"
            
            poor_body = (
                "NO ALERT (SEPTEMBER 4 BENCHMARK NOT MET):\n"
                "The upcoming 72-hour forecast does not offer conditions significantly better than your September 4 visit.\n\n"
                "--- AI Comparison & Reasoning ---\n"
                f"{analysis}"
            )
            
            send_email_alerts(subject, poor_body, RECIPIENT_EMAILS)
