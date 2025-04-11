import os
import time
import webbrowser
import pyautogui
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import shutil

# Configurazione
HTML_FILE = os.path.join("giornale", "giornale.html")
LOCAL_IMAGE_FOLDER = os.path.join("giornale", "images")
SERVER_IP = "192.168.3.92"
SERVER_IMAGE_FOLDER = "images_giornalino"
SERVER_URL = f"http://{SERVER_IP}/{SERVER_IMAGE_FOLDER}"
UPDATE_INTERVAL = 300  # 5 minuti in secondi
START_HOUR = 8  # 8:00 AM
END_HOUR = 14   # 2:00 PM

def download_images_from_server():
    """Scarica le immagini dal server alla cartella locale"""
    try:
        # Crea la cartella locale se non esiste
        if not os.path.exists(LOCAL_IMAGE_FOLDER):
            os.makedirs(LOCAL_IMAGE_FOLDER)
        
        # Pulisci la cartella locale
        for filename in os.listdir(LOCAL_IMAGE_FOLDER):
            file_path = os.path.join(LOCAL_IMAGE_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Errore cancellazione {file_path}: {e}")

        # Ottieni la lista delle immagini dal server
        response = requests.get(SERVER_URL + "/")
        if response.status_code != 200:
            print(f"Errore accesso server: {response.status_code}")
            return False

        # Parsing della directory (semplificato)
        # Nota: Questo dipende da come il server mostra i file
        # Potrebbe essere necessario adattarlo al tuo server specifico
        image_files = [f for f in response.text.split('\n') if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

        # Scarica ogni immagine
        for img_file in image_files:
            img_url = f"{SERVER_URL}/{img_file}"
            local_path = os.path.join(LOCAL_IMAGE_FOLDER, img_file)
            
            try:
                with requests.get(img_url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                print(f"Scaricato: {img_file}")
            except Exception as e:
                print(f"Errore download {img_file}: {e}")

        return True

    except Exception as e:
        print(f"Errore durante il download: {e}")
        return False

def update_html_images():
    """Aggiorna le immagini nell'HTML con quelle scaricate"""
    try:
        with open(HTML_FILE, 'r+', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            
            carousels = soup.find_all(class_='article-carousel')
            available_images = [f for f in os.listdir(LOCAL_IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
            
            if not available_images:
                print("Nessuna immagine disponibile localmente")
                return False
                
            for carousel in carousels:
                for slide in carousel.find_all(class_='carousel-slide'):
                    slide.decompose()
                
                for _ in range(min(3, len(available_images))):
                    img_name = random.choice(available_images)
                    new_slide = soup.new_tag('div', **{'class': 'carousel-slide'})
                    new_img = soup.new_tag('img', src=f'images/{img_name}', alt='News Image', style='width:100%; height:auto;')
                    new_slide.append(new_img)
                    carousel.append(new_slide)
            
            file.seek(0)
            file.write(str(soup))
            file.truncate()
            
        print("HTML aggiornato con nuove immagini")
        return True
        
    except Exception as e:
        print(f"Errore aggiornamento HTML: {e}")
        return False

def open_fullscreen():
    """Apre il browser a schermo intero"""
    try:
        # Chiudi browser esistenti
        if os.name == 'nt':
            os.system("taskkill /im chrome.exe /f")
            os.system("taskkill /im msedge.exe /f")
            os.system("taskkill /im firefox.exe /f")
        time.sleep(2)
        
        webbrowser.open('file://' + os.path.abspath(HTML_FILE))
        time.sleep(5)
        pyautogui.hotkey('f11')
        print(f"Visualizzazione avviata - {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"Errore apertura schermo intero: {e}")

def should_run():
    """Controlla se siamo nell'orario di funzionamento"""
    now = datetime.now()
    return START_HOUR <= now.hour < END_HOUR

def main():
    print("=== Sistema di Visualizzazione Automatico ===")
    print(f"Configurazione:")
    print(f"- Server: {SERVER_URL}")
    print(f"- Cartella locale: {LOCAL_IMAGE_FOLDER}")
    print(f"- Orario: {START_HOUR}:00 - {END_HOUR}:00")
    print(f"- Aggiornamento ogni: {UPDATE_INTERVAL//60} minuti\n")
    
    try:
        while True:
            if should_run():
                # Scarica e aggiorna le immagini
                if download_images_from_server() and update_html_images():
                    open_fullscreen()
                
                # Attendi fino alla prossima esecuzione o fine orario
                next_update = datetime.now() + timedelta(seconds=UPDATE_INTERVAL)
                while datetime.now() < next_update and should_run():
                    time.sleep(60)  # Controlla ogni minuto
                
                # Ricarica se siamo ancora nell'orario
                if should_run():
                    pyautogui.hotkey('f5')
                    time.sleep(2)
                    pyautogui.hotkey('f11')
            else:
                # Fuori orario - aspetta fino alle 8:00
                now = datetime.now()
                if now.hour >= END_HOUR:
                    tomorrow = now + timedelta(days=1)
                    next_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, START_HOUR)
                else:
                    next_start = datetime(now.year, now.month, now.day, START_HOUR)
                
                wait_seconds = (next_start - now).total_seconds()
                print(f"Fuori orario. Prossimo avvio alle {next_start.strftime('%H:%M')}")
                time.sleep(min(wait_seconds, 3600))  # Aspetta al massimo 1 ora
                
    except KeyboardInterrupt:
        print("\nProgramma interrotto manualmente")

if __name__ == "__main__":
    # Verifica struttura cartelle
    if not os.path.exists(LOCAL_IMAGE_FOLDER):
        os.makedirs(LOCAL_IMAGE_FOLDER)
    
    if not os.path.exists(HTML_FILE):
        print(f"Errore: File HTML non trovato in {HTML_FILE}")
        exit()
    
    main()