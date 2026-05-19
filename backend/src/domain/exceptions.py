class RoomTransitionError(ValueError):
    pass


class SongTransitionError(ValueError):
    pass


class RoomNotFoundError(ValueError):
    pass


class RoomNotJoinableError(ValueError):
    pass


class NicknameAlreadyTakenError(ValueError):
    pass


class RoomNotWaitingError(ValueError):
    pass


class RoundNotFoundError(ValueError):
    pass


class RoundNotInProgressError(ValueError):
    pass


class SongNotFoundError(ValueError):
    pass


class SongNotPlayableError(ValueError):
    pass


class SongNotLockableError(ValueError):
    pass


class SongNotAcceptingAnswersError(ValueError):
    pass


class SongNotLockedError(ValueError):
    pass


class NotHostError(ValueError):
    pass


class InvalidHostTokenError(NotHostError):
    pass


class AnswerNotFoundError(ValueError):
    pass


class SongNotCorrectableError(ValueError):
    pass


class SongNotRevealableError(ValueError):
    pass


class RoomNotFinishedRoundError(ValueError):
    pass
