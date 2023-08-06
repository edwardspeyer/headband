from pathlib import Path
from headband import add
from argparse import ArgumentParser


parser = ArgumentParser()

parser.add_argument("--username")
parser.add_argument("--password")
parser.add_argument("--domain", action="append")
parser.add_argument("--ip-address")
parser.add_argument("zonefile", nargs="*", type=Path)

args = parser.parse_args()
domains = list(args.domain)
zones = [z.read_text() for z in args.zonefile]
add(args.username, args.password, args.ip_address, domains, zones,)
