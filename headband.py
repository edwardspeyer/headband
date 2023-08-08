import shelve
from dataclasses import dataclass
from typing import Union
from contextlib import contextmanager
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://dns.he.net/"

RType = str
AAAA: RType = "AAAA"
A: RType = "A"
AFSDB: RType = "AFSDB"
ALIAS: RType = "ALIAS"
CAA: RType = "CAA"
CNAME: RType = "CNAME"
HINFO: RType = "HINFO"
LOC: RType = "LOC"
MX: RType = "MX"
NAPTR: RType = "NAPTR"
NS: RType = "NS"
PTR: RType = "PTR"
RP: RType = "RP"
SOA: RType = "SOA"
SPF: RType = "SPF"
SRV: RType = "SRV"
SSHFP: RType = "SSHFP"
TXT: RType = "TXT"


@dataclass(eq=True, frozen=True)
class RR:
    rname: str
    ttl: int
    rtype: RType
    rdata: Union[str | tuple[int, str]]


def sync(username, password, domain, rrs):
    with build_session() as session:
        response = session.get(URL)
        if b"Account Menu" not in response.content:
            response = session.post(
                URL,
                {
                    "email": username,
                    "pass": password,
                    "submit": "Login!",
                },
            )
        assert b"Account Menu" in response.content
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
            if rr.rtype == SOA:
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
        id, rname, rtype, ttl, priority, rdata = fields[1:7]
        if rtype == MX:
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
    if rr.rtype == MX:
        priority, rdata = rr.rdata
    else:
        priority, rdata = "", rr.rdata
    assert rr.ttl >= 300
    session.post(
        URL,
        {
            "account": "",
            "menu": "edit_zone",
            "Type": rr.rtype,
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
    path = Path.home() / ".local" / "share" / "headband.db"
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


def parse_html(html):
    return BeautifulSoup(html, features="lxml")


def parse_table(table_element):
    for row in table_element.select("tbody tr"):
        domain = row.select_one("span").string
        assert "." in domain, f"not a domain? {domain}"
        domain_id = row.select_one("img[alt=delete]")["value"]
        assert domain_id.isnumeric(), f"not a domain ID? {id}"
        yield domain, int(domain_id)
