from enum import Enum


class RoomStatus(str, Enum):
    CREATED = "created"
    WAITING = "waiting"
    ROUND_IN_PROGRESS = "round_in_progress"
    REVEAL = "reveal"
    ROUND_FINISHED = "round_finished"
    FINISHED = "finished"


class RoundStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class SongStatus(str, Enum):
    UPCOMING = "upcoming"
    PLAYING = "playing"
    LOCKED = "locked"
    VALIDATION = "validation"
    REVEALED = "revealed"
    SCORED = "scored"


class ValidationStatus(str, Enum):
    NOT_FOUND = "not_found"
    FOUND = "found"
    DOUBTFUL = "doubtful"
