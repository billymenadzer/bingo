import os
import sys
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from supabase import create_client, Client
import pytz
from datetime import datetime

print("🚀 Start robota Kambo-Skynet...")

# 1. Konfiguracja kluczy - zmuszamy skrypt do pobrania ich bezposrednio z serwera
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# TEST BEZPIECZEŃSTWA: Sprawdzamy czy maszyna w ogole widzi klucze (nie wypisujemy hasla!)
if not SUPABASE_URL:
    print("❌ BŁĄD: Skrypt nie widzi SUPABASE_URL! Zatrzymuję.")
    sys.exit(1)
if not SUPABASE_KEY:
    print("❌ BŁĄD: Skrypt nie widzi SUPABASE_KEY! Zatrzymuję.")
    sys.exit(1)
if not GEMINI_API_KEY:
    print("❌ BŁĄD: Skrypt nie widzi GEMINI_API_KEY! Zatrzymuję.")
    sys.exit(1)

print(f"🔗 Otrzymano URL z bazy: {SUPABASE_URL}")

# Podlaczamy Baze
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Połączono z Supabase!")
except Exception as e:
    print(f"❌ Blad polaczenia z Supabase: {e}")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
