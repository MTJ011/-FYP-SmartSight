from controllers.scanner_controller import start_scanner
from services.database_service import init_db

init_db()

start_scanner()