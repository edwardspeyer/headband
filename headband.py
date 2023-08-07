import shelve
from dataclasses import dataclass
from enum import Enum, auto
from typing import Union
from contextlib import contextmanager
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://dns.he.net/"


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


def sync(username, password, domain, rrs):
    with build_session() as session:
        ensure_logged_in(session, username, password)
        response = session.get(URL)
        doc = parse_html(response.content)
        table = doc.select_one("#domains_table")
        domains = dict(parse_table(table)) if table else dict()
        if domain in domains:
            zone_id = domains[domain]
        else:
            zone_id = add_domain(session, domain)

        response = session.get(
            URL,
            params={
                "hosted_dns_zoneid": zone_id,
                "hosted_dns_editzone": "",
                "menu": "edit_zone",
            },
        )
        doc = parse_html(response.content)
        current_rrs = dict(parse_rrs(doc))

        for rr, id in current_rrs.items():
            if rr.rtype == RType.SOA:
                continue
            if rr not in rrs:
                print(f"- {rr}")
                del_rr(session, zone_id, id)

        for rr in rrs:
            if rr not in current_rrs:
                print(f"+ {rr}")
                add_rr(session, zone_id, rr)


def parse_rrs(doc):
    for row in doc.select(".dns_tr_locked, .dns_tr"):
        fields = [v.text for v in row.select("td")]
        id, rname, rtype_name, ttl, priority, rdata = fields[1:7]
        rtype = RType[rtype_name]
        if rtype == RType.MX:
            assert priority.isnumeric()
            rr = RR(rname, int(ttl), rtype, (int(priority), rdata))
        else:
            assert priority == "-"
            rr = RR(rname, int(ttl), rtype, rdata)
        yield rr, id


def add_domain(session, domain):
    response = session.post(
        URL,
        {
            "action": "add_zone",
            "retmain": "0",
            "add_domain": domain,
            "submit": "Add Domain!",
        },
    )
    table = parse_html(response.content).select_one("#domains_table")
    domains = dict(parse_table(table))
    return domains[domain]


def add_rr(session, zone_id, rr):
    if rr.rtype == RType.MX:
        priority, rdata = rr.rdata
    else:
        priority, rdata = "", rr.rdata
    assert rr.ttl >= 300
    session.post(
        URL,
        {
            "account": "",
            "menu": "edit_zone",
            "Type": rr.rtype.name,
            "hosted_dns_zoneid": zone_id,
            "hosted_dns_recordid": "",
            "hosted_dns_editzone": "1",
            "Priority": priority,
            "Name": rr.rname,
            "Content": rdata,
            "TTL": str(rr.ttl),
            "hosted_dns_editrecord": "Submit",
        },
    )


def del_rr(session, zone_id, rr_id):
    session.post(
        URL,
        {
            "hosted_dns_zoneid": str(zone_id),
            "hosted_dns_recordid": str(rr_id),
            "menu": "edit_zone",
            "hosted_dns_delconfirm": "delete",
            "hosted_dns_editzone": "1",
            "hosted_dns_delrecord": "1",
        },
    )


@contextmanager
def build_session():
    path = Path.home() / ".local" / "share" / "aura" / "he.db"
    path.parent.mkdir(exist_ok=True, parents=True)
    key = "cookies"
    with shelve.open(path) as shelf:
        session = requests.Session()
        if data := shelf.get(key):
            cookies = requests.utils.cookiejar_from_dict(data)
            session.cookies.update(cookies)
        yield session
        data = requests.utils.dict_from_cookiejar(session.cookies)
        shelf[key] = data


def ensure_logged_in(session, username, password):
    response = session.get(URL)
    if b"Account Menu" in response.content:
        return
    print("logging in...")
    session.post(
        URL,
        {
            "email": username,
            "pass": password,
            "submit": "Login!",
        },
    )


def parse_html(html):
    return BeautifulSoup(html, features="lxml")


def parse_table(table_element):
    for row in table_element.select("tbody tr"):
        domain = row.select_one("span").string
        assert "." in domain, f"not a domain? {domain}"
        domain_id = row.select_one("img[alt=delete]")["value"]
        assert domain_id.isnumeric(), f"not a domain ID? {id}"
        yield domain, int(domain_id)
