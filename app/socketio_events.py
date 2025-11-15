"""Gestionnaire d'événements SocketIO pour les communications en temps réel"""
from flask import session
from flask_socketio import emit, join_room, leave_room
from app import socketio
import logging

logger = logging.getLogger(__name__)


@socketio.on('connect')
def handle_connect():
    """Gère la connexion d'un client"""
    logger.info(f"Client connecté: {session.get('socketio_sid', 'Unknown')}")
    emit('connected', {'data': 'Connexion établie'})


@socketio.on('disconnect')
def handle_disconnect():
    """Gère la déconnexion d'un client"""
    logger.info(f"Client déconnecté: {session.get('socketio_sid', 'Unknown')}")


@socketio.on('join_task')
def handle_join_task(data):
    """Permet à un client de rejoindre une room de tâche spécifique"""
    task_id = data.get('task_id')
    if task_id:
        join_room(task_id)
        logger.info(f"Client joint la room de tâche: {task_id}")
        emit('joined', {'task_id': task_id}, room=task_id)


@socketio.on('leave_task')
def handle_leave_task(data):
    """Permet à un client de quitter une room de tâche"""
    task_id = data.get('task_id')
    if task_id:
        leave_room(task_id)
        logger.info(f"Client a quitté la room de tâche: {task_id}")


def emit_progress(task_id, progress, message='', status='running'):
    """
    Émet une mise à jour de progression

    Args:
        task_id: ID de la tâche
        progress: Pourcentage de progression (0-100)
        message: Message descriptif
        status: Statut ('running', 'completed', 'error')
    """
    socketio.emit('progress_update', {
        'task_id': task_id,
        'progress': progress,
        'message': message,
        'status': status
    }, room=task_id)

    logger.info(f"Progression émise pour {task_id}: {progress}% - {message}")
