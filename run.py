"""Point d'entrée de l'application Flask"""
import os
from app import create_app

# Création de l'application
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Configuration du serveur de développement
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    )
