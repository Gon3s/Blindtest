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
