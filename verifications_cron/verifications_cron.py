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

def render_table_image(data_source, columns) -> bytes:
    headers = [c["title"] for c in columns]
    keys    = [c["dataIndex"] for c in columns]
    aligns  = [c.get("align","left") for c in columns]
    widths  = [int(c.get("width", 350)) for c in columns]

    def wrap(s: str, max_chars: int) -> str:
        s = "" if s is None else str(s)
        return "\n".join(textwrap.wrap(s, width=max_chars, break_long_words=False)) or ""

    def chars_for_width(px: int) -> int:
        return max(0, int(px / 7.5) - 2)

    name_chars = chars_for_width(widths[0])
    body = []
    row_line_counts = []
    for row in data_source:
        cells, lines_this_row = [], 1
        for j, k in enumerate(keys):
            val = row.get(k, "")
            if k == "name":
                val = wrap(val, name_chars)
            else:
                val = str(val)
            cells.append(val)
            lines_this_row = max(lines_this_row, val.count("\n") + 1)
        body.append(cells)
        row_line_counts.append(lines_this_row)

    dpi = 200
    total_px_w = max(1000, sum(widths))
    col_width_fracs = [w / total_px_w for w in widths]

    header_px = 60
    base_row_px = 60
    extra_line_px = 16
    row_heights_px = [
        base_row_px + (lc - 1) * extra_line_px
        for lc in row_line_counts
    ]
    total_px_h = header_px + sum(row_heights_px)

    fig_w = total_px_w / dpi
    fig_h = total_px_h / dpi
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.axis("off")

    tbl = ax.table(
        cellText=body,
        colLabels=headers,
        loc="upper left",
        colWidths=col_width_fracs,
        cellLoc="left",
        rowLoc='left'
    )

    fs = 12
    tbl.auto_set_font_size(True)
    tbl.set_fontsize(fs)

    header_color = "#f5f5f5"
    border_color = "#d9d9d9"
    cell_border_color = "#e6e6e6"
    stripe_color = "#fafafa"
    header_frac = header_px / total_px_h
    row_fracs = [px / total_px_h for px in row_heights_px]

    for j in range(len(headers)):
        cell = tbl[0, j]
        cell.set_facecolor(header_color)
        cell.get_text().set_weight("bold")
        cell.set_edgecolor(border_color)
        cell.get_text().set_rotation(0)
        cell.set_height(header_frac)

    n_rows = len(body)
    for i in range(1, n_rows + 1):
        row_fc = stripe_color if (i % 2 == 0) else "white"
        for j in range(len(headers)):
            cell = tbl[i, j]
            cell.set_facecolor(row_fc)
            cell.set_edgecolor(cell_border_color)
            ha = "left" if aligns[j] == "left" else "center" if aligns[j] == "center" else "right"
            t = cell.get_text()
            t.set_ha(ha)
            t.set_rotation(0)
            t.set_wrap(True)
            t.set_path_effects([patheffects.withStroke(linewidth=1, foreground="white")])
            cell.set_height(row_fracs[i - 1])

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    buf.seek(0)
    return buf.read()



def main():
    sess = session_with_retries()
    headers = {"x-api-key": METABASE_API_KEY, "Authorization": f"Basic {METABASE_AUTH_STRING}"}
    r = sess.post(METABASE_URL, headers=headers, data={}, timeout=15)
    r.raise_for_status()
    rows = r.json().get("data", {}).get("rows", []) or []

    titles = ["Nombre", "Estado", "Fecha"]
    keys   = ["name",  "status", "date"]

    data_source = []
    for row in rows:
        if len(row) < len(keys):
            row = row + [''] * (len(keys) - len(row))
        row_dict = {keys[i]: row[i] for i in range(len(keys))}
        row_dict["date"] = format_date(row_dict["date"])
        data_source.append(row_dict)

    if not data_source:
        return

    columns = [
        {
            "title": title,
            "dataIndex": keys[i],
            "width": 1000 if i == 0 else 350 if i == 1 else 450,
            "align": 'left' if i == 0 else 'center' if i == 1 else 'right',
        }
        for i, title in enumerate(titles)
    ]

    img = render_table_image(data_source, columns)

    # Post to Discord
    n_rows = len(data_source)
    filename = "tabla_alumnos_por_verificar.png"
    content  = f"Total de verificaciones pendientes: {n_rows}\nhttps://verification.open.uchile.cl/interface"
    payload = {"payload_json": json.dumps({"content": content})}
    files   = {"files[0]": (filename, img, "image/png")}
    resp = sess.post(DISCORD_WEBHOOK_URL, data=payload, files=files, timeout=30)
    resp.raise_for_status()

if __name__ == "__main__":
    main()
