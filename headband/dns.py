from dataclasses import dataclass
from enum import Enum, auto
from typing import Union


class RType(Enum):
    AAAA = auto()
    A = auto()
    AFSDB = auto()
    ALIAS = auto()
    CAA = auto()
    CNAME = auto()
    HINFO = auto()
    LOC = auto()
    MX = auto()
    NAPTR = auto()
    NS = auto()
    PTR = auto()
    RP = auto()
    SOA = auto()
    SPF = auto()
    SRV = auto()
    SSHFP = auto()
    TXT = auto()


@dataclass(eq=True, frozen=True)
class RR:
    rname: str
    ttl: int
    rtype: RType
    rdata: Union[str | tuple[int, str]]
