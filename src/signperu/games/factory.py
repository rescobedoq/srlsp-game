#src/signperu/games/factory.py
from .juego_ah import JuegoAH
from .juego_ladrillos import JuegoLadrillos
from .juego_lc import JuegoLC

class GameFactory:
    @staticmethod
    def create(game_id, user, event_queue, db):
        if game_id == 'AH':
            return JuegoAH(user, event_queue, db)
        if game_id == 'LADRILLOS':
            return JuegoLadrillos(user, event_queue, db)
        if game_id == 'LC':
            return JuegoLC(user, event_queue, db)
        raise ValueError('Unknown game id: %s' % game_id)
