from enum import Enum


class SetStatus(Enum):
    ACCESS_READY = 1
    ACCESS_RETRY_GET = 3
    ACCESS_ACTIVATION = 6
    ACCESS_CANCEL = 8


class GetStatus(Enum):
    WAIT_CODE = 'STATUS_WAIT_CODE'
    WAIT_RETRY = 'STATUS_WAIT_RETRY'
    CANCEL = 'STATUS_CANCEL'
    OK = 'STATUS_OK'
