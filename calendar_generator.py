import requests
from bs4 import BeautifulSoup
import ics
from ics import Calendar, Event
from datetime import datetime, timedelta
from dateutil.tz import gettz
MONTHS = {
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
        'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
        'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
    }

def fetch_calendar_data(url):
    """Recupera i dati dal calendario del Post"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Errore nel recupero della pagina: {response.status_code}")
    return response.text

def parse_events(html_content):
    """Estrae gli eventi dal contenuto HTML di Il Post, robusto alle classi dinamiche."""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []

    with open("debug_ilpost.html", "w", encoding="utf-8") as debug_file:
        debug_file.write(soup.prettify())

    # Trova tutti i container degli eventi che iniziano con "_single-event-featured"
    containers = soup.find_all("div", class_=lambda c: c and c.startswith("_single-event"))
    
    for container in containers:
        try:
            # --- DATE ---
            time_tag = container.find("time", class_=lambda c: c and c.startswith("_single-event__date"))
            if not time_tag:
                continue

            datetime_str = time_tag.get('datetime', '').strip()
            if not datetime_str:
                continue

            # Estrazione giorno, mese, anno
            day, month_name, year = datetime_str.split(" ")[0], datetime_str.split(" ")[1], datetime_str.split(" ")[2]
            month = MONTHS.get(month_name.lower(), 1)
            year = int("20" + year.replace(",", ""))

            # --- TIME & LOCATION ---
            details_div = container.find("div", class_=lambda c: c and c.startswith("_single-event__details"))
            if details_div:
                spans = details_div.find_all("span")
                if len(spans) >= 2:
                    time_text = spans[0].text.strip()
                    location_text = details_div.contents[-1].strip()
                    hour, minute = map(int, time_text.split(":"))
                else:
                    hour = minute = 0
                    location_text = ""
            else:
                hour = minute = 0
                location_text = ""

            dt = datetime(year, month, int(day), hour, minute, tzinfo=gettz('Europe/Rome'))

            # --- TITLE & SUBTITLE ---
            title_tag = container.find("h4")
            title = title_tag.text.strip() if title_tag else "Evento senza titolo"

            subtitle_tag = container.find("div", class_=lambda c: c and c.startswith("_single-event__subtitle"))
            subtitle = subtitle_tag.text.strip() if subtitle_tag else ""

            # --- DESCRIPTION ---
            description_tag = container.find("div", class_=lambda c: c and c.startswith("_single-event__summary"))
            description = description_tag.text.strip() if description_tag else ""

            # --- LINKS ---
            actions_div = container.find("div", class_=lambda c: c and c.startswith("_single-event__actions"))
            ticket_link = None
            more_info_link = None
            if actions_div:
                ticket_tag = actions_div.find("a", class_=lambda c: c and "_book-button" in c)
                ticket_link = ticket_tag.get("href") if ticket_tag else None

                info_tag = actions_div.find("a", class_=lambda c: c and "_event-more-info" in c)
                more_info_link = info_tag.get("href") if info_tag else None

            # --- CREATE EVENT DICTIONARY ---
            print(f"Parsing evento: {title} il {dt} a {location_text}")
            print(f" - Descrizione: {description}")
            print(f" - Link biglietti: {ticket_link}")
            print(f" - Link info: {more_info_link}")
            
            event = {
                'title': title,
                'description': description,
                'date': dt,
                'location': location_text,
                'notes': subtitle,
                'link': more_info_link
            }

            events.append(event)

        except Exception as e:
            print(f"Errore nel parsing di un evento: {e}")
            continue

    return events

def create_ics_calendar(events):
    """Crea un calendario ICS dagli eventi"""
    cal = Calendar()
    
    for event_data in events:
        event = Event(
            alarms=[ics.alarm.DisplayAlarm(trigger=timedelta(days=1))]
        )
        event.name = event_data['title']
        event.description = event_data['description']
        
        # Imposta la data di inizio e fine (assumiamo che gli eventi durino un giorno)
        event.begin = event_data['date']
        event.end = event_data['date'] + timedelta(hours=4)
        if event_data['date'].tzinfo is None:
            event_data['date'] = gettz('Europe/Rome').localize(event_data['date'])
        event.location = event_data['location']
        event.description = event_data['notes']
        event.url = event_data['link']
                
        # Aggiungi l'evento al calendario
        cal.events.add(event)
    
    return cal

def save_calendar(calendar, filename):
    """Salva il calendario in un file"""
    with open(filename, 'w') as f:
        f.write(str(calendar.serialize()))

def main():
    url = "https://www.ilpost.it/calendario/"
    output_file = "calendario_ilpost.ics"
    
    try:
        html_content = fetch_calendar_data(url)
        events = parse_events(html_content)
        
        if not events:
            print("Nessun evento trovato. Verifica la struttura della pagina.")
            return
        
        calendar = create_ics_calendar(events)
        save_calendar(calendar, output_file)
        
        print(f"Calendario creato con successo: {output_file}")
        print(f"Numero di eventi estratti: {len(events)}")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    main()