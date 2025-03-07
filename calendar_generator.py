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
    """Estrae gli eventi dal contenuto HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    events = []
    
    # Trova i container degli eventi
    event_containers = soup.find('div', attrs={"id": "main"})
    event_containers = event_containers.find_all('div', attrs={"class": "row"})[1]
    event_containers = event_containers.find('div', attrs={"class": "col-xl-12"})
    event_containers = event_containers.find_all('div')
    
    for container in event_containers:
        time = container.find('time')
        if not time:
            continue
        time = time.get('datetime')
        details = container.find('details')
        
        summary = details.find('summary')
        location_time = summary.find_all('div')[1]
        eventtime = location_time.find('span')
        if eventtime:
            hour = int(eventtime.text.split(":")[0])
            minute = int(eventtime.text.split(":")[1])
            
        dt = datetime(day=int(time.split(" ")[0]),
                      month=MONTHS[time.split(" ")[1]],
                      year=int("20"+time.split(" ")[2].replace(",","")),
                      hour=hour if hour is not None else 0,
                      minute=minute if minute is not None else 0,
                      tzinfo=gettz('Europe/Rome'))
        title = summary.find('div').find('span').text
        description = summary.find('h4').text
        location = location_time.text
        if ":" in location[:5]:
            location = location[5:]
        print(dt)
        print(title)
        print(description)
        print(location)
        
        # Crea oggetto evento
        event = {
            'title': title,
            'description': description,
            'date': dt,
            'location': location
        }
            
        events.append(event)
        
    
    return events

def create_ics_calendar(events):
    """Crea un calendario ICS dagli eventi"""
    cal = Calendar()
    
    for event_data in events:
        event = Event()
        event.name = event_data['title']
        event.description = event_data['description']
        
        # Imposta la data di inizio e fine (assumiamo che gli eventi durino un giorno)
        event.begin = event_data['date']
        event.end = event_data['date'] + timedelta(hours=8)
        if event_data['date'].tzinfo is None:
            event_data['date'] = gettz('Europe/Rome').localize(event_data['date'])
        event.location = event_data['location']
        
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