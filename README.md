# Round-Robin Webmail Balancer

Flask app that redirects privileged emails to a rotating pool of webmail backends,
and sends everyone else to DocuSign.

## Files

- `app.py` — Flask application; loads privileged emails and handles routing.
- `emails.txt` — privileged email list, one address per line. Blank lines and lines
  starting with `#` are ignored. Edit this file to add/remove addresses.
- `requirements.txt` — Python dependencies.
- `vercel.json` — Vercel config (ensures `emails.txt` is bundled with the function).

## Run locally

```bash
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:5000/#your@email.com