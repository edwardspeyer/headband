# headband

Programmatically sync domains to Hurricane Electric's primary DNS service.

```python
import headband
from headband.dns import RR, RType

zone = [
    RR("example.com", 172800, RType.NS, "ns1.he.net"),
    RR("example.com", 172800, RType.NS, "ns2.he.net"),
    RR("example.com", 172800, RType.NS, "ns3.he.net"),
    RR("example.com", 172800, RType.NS, "ns4.he.net"),
    RR("example.com", 172800, RType.NS, "ns5.he.net"),
    RR("www.example.com", 300, RType.CNAME, "server.example.com."),
    RR("mail.example.com", 300, RType.CNAME, "server.example.com."),
    RR("server.example.com", 300, RType.A, "192.168.1.1"),
]

headband.sync(
    "uSeRnAmE",
    "PaSsWoRd",
    "example.com"
    zone,
)
```

Thank you, Hurricane Electric xx
