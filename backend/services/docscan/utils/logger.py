from datetime import datetime

def log(message):

    timestamp = datetime.now()

    print(
        f"[{timestamp}] {message}"
    )