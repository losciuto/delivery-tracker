import msal
import webbrowser
import time
import os
import sys

# Aggiungi il percorso corrente per caricare i moduli locali
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils

# OAuth2 Settings
CLIENT_ID = "3932ab49-e115-44d6-964e-9b43a479c5bd"
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["https://outlook.office.com/IMAP.AccessAsUser.All"]

def authorize():
    """Start interactive OAuth2 flow"""
    settings = utils.Settings.load()
    token_cache = msal.SerializableTokenCache()
    
    # Load cache if exists
    cache_data = settings.get('ms_token_cache')
    if cache_data:
        token_cache.deserialize(cache_data)
        
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=token_cache)
    
    print("Inizializzazione flusso di autorizzazione...")
    result = None

    try:
        # Try Interactive Flow first (opens browser and waits for redirect)
        # Port 0 means MSAL will find an available port
        print("Tentativo di autenticazione interattiva...")
        result = app.acquire_token_interactive(scopes=SCOPES, port=0)
    except Exception as e:
        print(f"L'autenticazione interattiva non è riuscita o non è supportata: {e}")
        print("Passaggio al Device Flow...")
        
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            error_msg = flow.get("error_description") or flow.get("error") or "Errore sconosciuto"
            print(f"ERRORE MICROSOFT: {error_msg}")
            if "AADSTS70002" in error_msg:
                print("\nSCADENZA CONFIGURAZIONE!")
                print("Devi abilitare 'Public client flows' nel portale Azure:")
                print("1. Vai in 'Autenticazione'")
                print("2. In fondo, imposta 'Consenti flussi di client pubblici' su SÌ.")
            raise ValueError(f"Impossibile avviare il dispositivo di flusso: {error_msg}")
            
        print(f"Vai su: {flow['verification_uri']}")
        print(f"Inserisci il codice: {flow['user_code']}")
        webbrowser.open(flow['verification_uri'])
        result = app.acquire_token_by_device_flow(flow)
    
    if result and "access_token" in result:
        print("Autorizzazione completata con successo!")
        settings['ms_token_cache'] = token_cache.serialize()
        settings['email_address'] = result.get('id_token_claims', {}).get('preferred_username')
        utils.Settings.save(settings)
        return True
    else:
        desc = result.get('error_description') if result else "Nessuna risposta dal server"
        print(f"Errore durante l'autorizzazione: {desc}")
        return False

if __name__ == "__main__":
    authorize()
