import os
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from supabase import create_client, Client
import pytz
from datetime import datetime

print("🚀 Start robota Kambo-Skynet...")

# 1. Konfiguracja kluczy z sejfu GitHuba
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# Słownik 70 haseł
all_phrases = [
    "szkola surykatki", "Adam", "Spotkanie biznesowe", "prysznic", "Junku gdzie jestes", 
    "jedzenie dla Junku", "Angkor Wat", "rynek", "pracownicy", "robaki dla surykatek", 
    "mamy Gosci", "Asia sie nagrywa", "Asia patrzy z pogarda", "ooo kotki!", 
    "niestety ale....", "ulewa", "zupa", "inwestor", "nie sprzedaje farmy", 
    "sprzedaje farme", "mama juny", "Alan i Eco", "Ewa", "przepraszam panstwa ale...", 
    "Brenda", "nic nie jadlem", "pySZne jedzonko", "basen", "biznes lubi cisze", 
    "musicie Panstwo zrozumiec...", "sklep z filtrami", "nasze kiszonki", "burgery", 
    "paluchy w zblizeniu", "lekarz / szpital/ cisnienie", "motocykl", "mamy problem", 
    "sklep AQ", "fryzjer", "zakupy odziezowe", "nowe buty", "problem z pradem", 
    "praoblem z internetem", "urodziny juny", "Tharong", "Wujek od giftow", 
    "prezenty", "zli khmerzy", "nowe koszulki", "plaszcz przecideszczowy", 
    "musze zatankowac", "kawa/ekpres do kawy", "musze jechac", "musze kupic", 
    "poliakov", "zawleczki cambodia", "pani z kiosku", "zeby paszport", 
    "problemy z cisnieniem", "przyjechal wujek", "robie pranie", "noodle dla Junku", 
    "zalalo nas", "zabraklo ryzu", "nie wiem gdzie jest Juny", "spotkanie po za kamerami", 
    "Grill", "dary losu", "pokazywanie cen", "Haussman"
]

winning_lines = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]]

try:
    # 2. Pobieramy najnowszy odcinek z kanału "Po pas w pieprz"
    print("📺 Szukam najnowszego odcinka na kanale...")
    videos = scrapetube.get_channel(channel_url="https://www.youtube.com/@popaswpieprz")
    latest_video = next(videos)
    video_id = latest_video['videoId']
    print(f"✅ Znaleziono wideo: https://www.youtube.com/watch?v={video_id}")

    # 3. Pobieramy transkrypcję
    print("📝 Pobieranie ukrytych napisów (transkrypcji)...")
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pl'])
    transcript_text = " ".join([t['text'] for t in transcript_list])

    # 4. Analiza sztuczną inteligencją (Gemini)
    print("🧠 Wysyłam dane do AI w celu analizy...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Jesteś analitykiem kanału YouTube o nazwie "Po pas w pieprz" w Kambodży.
    Twoim zadaniem jest przeczytać poniższą transkrypcję z odcinka i wyłapać, które z naszych haseł Bingo w niej wystąpiły.
    
    Oto nasz sztywny słownik 70 haseł:
    {all_phrases}

    Oto transkrypcja:
    {transcript_text}

    Zwróć TYLKO I WYŁĄCZNIE listę trafionych haseł ze słownika, rozdzielonych przecinkiem. 
    Wypisz je dokładnie tak, jak są w słowniku. Żadnego wstępu, żadnego komentarza.
    """
    response = model.generate_content(prompt)
    ai_result = response.text.strip()
    official_fallen_phrases = [p.strip() for p in ai_result.split(',')]
    print(f"🎯 Hasła wyłapane przez AI: {official_fallen_phrases}")

    # 5. Aktualizacja bazy danych Bingo (Rozliczenie!)
    print("🧮 Rozpoczynam rozliczanie kuponów w Supabase...")
    tz = pytz.timezone('Europe/Warsaw')
    target_date = datetime.now(tz).strftime('%Y-%m-%d')
    
    kupony_response = supabase.table('kupony').select('*').eq('odcinek_data', target_date).execute()
    kupony = kupony_response.data
    
    if not kupony:
        print("⚠️ Brak kuponów na dzisiejszy dzień. Zamykam system.")
    else:
        processed_players = []
        for kupon in kupony:
            user_phrases = kupon['hasla']
            hits = 0
            matched_idx = []
            matched_text = []
            for idx, p in enumerate(user_phrases):
                if p in official_fallen_phrases:
                    hits += 1
                    matched_idx.append(idx)
                    matched_text.append(p)
            
            has_bingo = any(all(idx in matched_idx for idx in line) for line in winning_lines)
            
            processed_players.append({
                'nick': kupon['nick'],
                'score': hits,
                'hasBingo': has_bingo,
                'matchedTexts': ', '.join(matched_text)
            })
            
        processed_players.sort(key=lambda x: (x['hasBingo'], x['score']), reverse=True)
        
        supabase.table('ranking').insert([{'zwyciezcy': processed_players, 'odcinek_data': target_date}]).execute()
        print("👑 SUKCES! Kupony rozliczone, zapisane w Hall of Fame!")

except Exception as e:
    print(f"❌ WYSTĄPIŁ BŁĄD SYSTEMU: {e}")
