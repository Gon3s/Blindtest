from fastapi import Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AnswerNotFoundError,
    InvalidHostTokenError,
    NicknameAlreadyTakenError,
    NotHostError,
    RoomNotFinishedRoundError,
    RoomNotFoundError,
    RoomNotJoinableError,
    RoomNotWaitingError,
    RoomTransitionError,
    RoundNotFoundError,
    RoundNotInProgressError,
    SongNotAcceptingAnswersError,
    SongNotCorrectableError,
    SongNotFoundError,
    SongNotLockableError,
    SongNotLockedError,
    SongNotPlayableError,
    SongNotRevealableError,
    SongTransitionError,
)

_ERROR_MAP: dict[type[Exception], tuple[int, str, str]] = {
    RoomNotFoundError: (
        404, "room_not_found", "Code de salle invalide. Vérifie le code et réessaie."
    ),
    RoomNotJoinableError: (
        409,
        "room_already_started",
        "La partie a déjà commencé. Tu ne peux plus rejoindre.",
    ),
    NicknameAlreadyTakenError: (
        409, "nickname_taken", "Ce pseudo est déjà pris. Choisis-en un autre."
    ),
    RoomNotWaitingError: (409, "room_not_waiting", "La partie a déjà commencé."),
    RoomNotFinishedRoundError: (
        409, "round_not_finished", "La manche n'est pas encore terminée."
    ),
    RoundNotFoundError: (404, "round_not_found", "Manche introuvable."),
    RoundNotInProgressError: (409, "round_not_in_progress", "Aucune manche en cours."),
    SongNotFoundError: (404, "song_not_found", "Chanson introuvable."),
    SongNotPlayableError: (
        409, "song_not_playable", "Cette chanson ne peut pas être lancée."
    ),
    SongNotLockableError: (
        409, "song_not_lockable", "Cette chanson ne peut pas être verrouillée."
    ),
    SongNotAcceptingAnswersError: (
        409, "answer_too_late", "Trop tard ! La chanson est terminée."
    ),
    SongNotLockedError: (
        409, "song_not_locked", "La chanson n'est pas encore terminée."
    ),
    SongNotCorrectableError: (
        409, "song_not_correctable", "Les réponses ne peuvent plus être modifiées."
    ),
    SongNotRevealableError: (
        409, "song_not_revealable", "La chanson ne peut pas encore être révélée."
    ),
    NotHostError: (403, "not_host", "Action réservée à l'hôte."),
    AnswerNotFoundError: (404, "answer_not_found", "Réponse introuvable."),
    RoomTransitionError: (
        409, "room_transition_error", "Transition d'état impossible pour la salle."
    ),
    SongTransitionError: (
        409, "song_transition_error", "Transition d'état impossible pour la chanson."
    ),
}


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    for exc_type in type(exc).__mro__:
        if exc_type in _ERROR_MAP:
            status, code, message = _ERROR_MAP[exc_type]
            return JSONResponse(
                status_code=status, content={"code": code, "message": message}
            )
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "Une erreur inattendue s'est produite.",
        },
    )


HANDLED_EXCEPTIONS: tuple[type[Exception], ...] = tuple(_ERROR_MAP.keys())
