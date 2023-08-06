# headband

Configure Hurricane Electric DNS to serve your domains:

* Configure an `he.net` account so that HE acts as a secondary DNS server for
  your domain.
* Run a primary DNS server, temporarily, to serve dns.he.net's initial zone
  transfer request.

## TODO

It's probably quick to sync a zone by (1) asking he.net to be our primary DNS
then (2) using the HTTP API to add RRs.
