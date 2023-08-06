from bs4 import BeautifulSoup
from contextlib import contextmanager
from pathlib import Path
import shelve
import requests
from subprocess import run


def render(html):
    run(["w3m", "-dump", "-T", "text/html", "-"], input=html)


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
    response = session.get("https://dns.he.net/")
    if b"Account Menu" in response.content:
        return
    print("logging in...")
    session.post(
        "https://dns.he.net/",
        {
            "email": username,
            "pass": password,
            "submit": "Login!",
        },
    )


def parse_html(html):
    return BeautifulSoup(html, features="lxml")


def parse_domains_table(doc):
    for row in doc.select("#secondary_table tbody tr"):
        domain = row.select_one("span").string
        assert "." in domain, f"not a domain? {domain}"
        domain_id = row.select_one("img[alt=delete]")["value"]
        assert domain_id.isnumeric(), f"not a domain ID? {id}"
        yield domain, int(domain_id)


def parse_account(doc):
    return doc.select_one('input[name=account]').value


def add_slave_domain(username, password, domain, master):
    with build_session() as session:
        ensure_logged_in(session, username, password)
        response = session.get("https://dns.he.net/")
        doc = parse_html(response.content)

        domains = dict(parse_domains_table(doc))
        print(f"already known {domains=}")
        if domain_id := domains.get(domain):
            print(f"deleting existing {domain=}")
            session.post(
                "https://dns.he.net/index.cgi",
                {
                    "account": parse_account(doc),
                    "delete_id": domain_id,
                    "remove_domain": 1,
                }
            )

        print(f"adding {domain=}")
        params = {
            "action": "add_slave",
            "retmain": 0,
            "add_slave": domain,
            "master1": str(master),
            "master2": None,
            "master3": None,
            "algorithm": None,
            "keyname": None,
            "secret": None,
            "submit": "Add Slave!",
        }
        print(params)
        response = session.post("https://dns.he.net/index.cgi", params)

        if error := parse_html(response.content).select_one("#dns_err"):
            raise Exception(error.text)
