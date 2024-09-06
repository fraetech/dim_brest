#!/usr/bin/env python
from datetime import datetime
def log_message(message, level="INFO"):
    """Fonction de log pour afficher un timestamp avec le niveau d'erreur."""
    timestamp = datetime.now().strftime("%d/%m/%Y à %H:%M:%S")
    print(f"{timestamp} [{level}] -> {message}")