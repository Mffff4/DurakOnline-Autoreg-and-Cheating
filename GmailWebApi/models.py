from dataclasses import dataclass


@dataclass
class Cookie:
    name: str
    value: str
    domain: str


@dataclass
class Session:
    name: str
    email: str
    avatar: str
    index: int
    account_id: int
