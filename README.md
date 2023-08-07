# headband

Programmatically sync domains to Hurricane Electric's primary DNS service.

```python
from headband import CNAME, MX, NS, RR, A, sync

zone = [
    RR("example.com", 172800, NS, "ns1.he.net"),
    RR("example.com", 172800, NS, "ns2.he.net"),
    RR("example.com", 172800, NS, "ns3.he.net"),
    RR("example.com", 172800, NS, "ns4.he.net"),
    RR("example.com", 172800, NS, "ns5.he.net"),
    RR("example.com", 300, MX, (10, "mail.example.com")),  # NB priority
    RR("www.example.com", 300, CNAME, "server.example.com"),
    RR("mail.example.com", 300, CNAME, "server.example.com"),
    RR("server.example.com", 300, A, "192.168.1.1"),
]

sync(
    "uSeRnAmE",
    "PaSsWoRd",
    "example.com"
    zone,
)
```

Thank you, Hurricane Electric xx
