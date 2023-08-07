from argparse import ArgumentParser
from pathlib import Path

from headband import sync

parser = ArgumentParser()

parser.add_argument("username")
parser.add_argument("password")
parser.add_argument("domain")
parser.add_argument("zonefile", type=Path)

args = parser.parse_args()

sync(
    args.username,
    args.password,
    args.domain,
    args.zonefile.read_text(),
)
