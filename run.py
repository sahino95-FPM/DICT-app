"""Point d'entrée de l'application Flask"""
import os
from app import create_app, socketio

# Création de l'application
flask_app = create_app(os.getenv('FLASK_ENV', 'development'))

# Importer les événements SocketIO
import app.socketio_events

if __name__ == '__main__':
    # Configuration du serveur de développement avec SocketIO
    socketio.run(
        flask_app,
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=flask_app.config.get('DEBUG', True),
        allow_unsafe_werkzeug=True  # Pour le développement uniquement
    )
