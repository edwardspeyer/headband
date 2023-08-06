import socketserver
from time import time
import re
import struct
import dnslib
from threading import Thread
from queue import Queue


SOA_RNAME = "hostmaster"
SOA_TIMES = (60, 60, 604800, 300)

HE_NAMESERVERS = [
    "ns2.he.net.",
    "ns3.he.net.",
    "ns4.he.net.",
    "ns5.he.net.",
]


def serve_once(unqualified_domains, zones):
    domains = [_qualify(d) for d in unqualified_domains]
    q = Queue()
    rrs = [rr for zone in zones for rr in dnslib.RR.fromZone(zone)]
    server = _build(domains, rrs, q)
    Thread(target=server.serve_forever, daemon=True).start()
    consumer = Thread(target=_wait, args=[domains, q, server])
    consumer.start()
    return consumer


def _wait(domains, q, server):
    seen = set()
    # while seen != set(domains):
    while True:
        seen.add(q.get())
        print(f"{domains=} {seen=}")
    server.shutdown()


def _build(domains, rrs, q):
    start_time = time()

    def unpack(sock):
        data = sock.recv(8192).strip()
        header, data = data[:2], data[2:]
        size = struct.unpack(">H", header)[0]
        assert len(data) == size
        return dnslib.DNSRecord.parse(data)

    def pack(response):
        data = response.pack()
        header = struct.pack(">H", len(data))
        return header + data

    class ZoneTransferHandler(socketserver.StreamRequestHandler):
        def handle(self):
            print(self.client_address)
            request = unpack(self.request)
            if request.q.qtype != dnslib.QTYPE.AXFR:
                print(f"unable to respond to {request.q.qtype=}")
                return
            domain = str(request.q.qname)
            if domain not in domains:
                print(f"unknown {domain=}")
                return
            assert re.match(r"(\w+\.)+$", domain)
            header = dnslib.DNSHeader(
                id=request.header.id,
                qr=1,
                aa=1,
                ra=0,
                rd=0,
            )
            response = dnslib.DNSRecord(header, q=request.q)
            soa_rr = _build_soa_record(start_time, domain)
            ns_rrs = _build_ns_records(domain)
            response.add_answer(soa_rr, *ns_rrs, *rrs, soa_rr)
            self.request.send(pack(response))
            q.put(domain)

    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.ThreadingTCPServer(
        ("0.0.0.0", 53),
        ZoneTransferHandler,
    )
    return server


def _qualify(domain):
    if domain[-1] != '.':
        domain += '.'
    return domain


def _build_soa_record(mtime, domain):
    times = (int(mtime), *SOA_TIMES)
    return dnslib.RR(
        domain,
        rtype=dnslib.QTYPE.SOA,
        rdata=dnslib.SOA(HE_NAMESERVERS[0], SOA_RNAME, times),
    )


def _build_ns_records(domain):
    for host in HE_NAMESERVERS:
        yield dnslib.RR(
            domain,
            rtype=dnslib.QTYPE.NS,
            rdata=dnslib.NS(host),
        )
