import headband.named
import headband.he


def add(username, password, our_ip_address, domains, zones):
    for domain in domains:
        if domain[-1] == '.':
            raise Exception(f"do not qualify {domain=} with a period!")

    t = headband.named.serve_once(domains, zones)

    for domain in domains:
        headband.he.add_slave_domain(
            username,
            password,
            domain,
            our_ip_address
        )

    t.join()
