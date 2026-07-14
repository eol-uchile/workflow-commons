# bot_daily.py
import os, sys, io, json
import requests
import io, textwrap
from requests.adapters import HTTPAdapter, Retry
import matplotlib.pyplot as plt
from matplotlib import patheffects
from dateutil import parser

def need(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        print(f"Missing required env: {name}", file=sys.stderr)
        sys.exit(2)
    return v

METABASE_API_KEY        = need("METABASE_API_KEY")
METABASE_AUTH_STRING    = need("METABASE_AUTH_STRING")
METABASE_URL            = need("METABASE_URL")
DISCORD_WEBHOOK_URL     = need("DISCORD_WEBHOOK_URL")

def session_with_retries():
    s = requests.Session()
    retries = Retry(
        total=3, backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET","POST"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://",  HTTPAdapter(max_retries=retries))
    return s


def format_date(s: str) -> str:
    if not s:
        return ""
    s = str(s).strip().strip('"\'')
    dt = parser.isoparse(s)
    return dt.strftime("%d/%m/%Y %H:%M")

def main():
    sess = session_with_retries()
    headers = {"x-api-key": METABASE_API_KEY, "Authorization": f"Basic {METABASE_AUTH_STRING}"}
    r = sess.post(METABASE_URL, headers=headers, data={}, timeout=15)
    r.raise_for_status()
    data = r.json()
    n = int(data[0]['n_pendiente']) if data and 'n_pendiente' in data[0] else 0
    if n == 0:
        return

    # Post to Discord
    content  = f"Total de verificaciones pendientes: {n}\nhttps://verification.open.uchile.cl/interface"
    payload = {"payload_json": json.dumps({"content": content})}
    resp = sess.post(DISCORD_WEBHOOK_URL, data=payload, timeout=30)
    resp.raise_for_status()

if __name__ == "__main__":
    main()
