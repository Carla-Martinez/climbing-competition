import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Alcance necesario para Google Sheets y Drive
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Cargar credenciales
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)

# Listar todos los Google Sheets accesibles
spreadsheets = client.openall()
print("Hojas disponibles:")
for sheet in spreadsheets:
    print("-", sheet.title)
