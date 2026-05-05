# ── Dockerfile.test ───────────────────────────────────────────────────────────
# Runs the 20 Selenium test cases with headless Chrome.
# Built and executed by the Test stage in the Jenkinsfile.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim-bullseye

# ── System-level Chrome dependencies ─────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libgdk-pixbuf-xlib-2.0-0 libnspr4 libnss3 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils \
    libgbm1 libgtk-3-0 libxkbcommon0 libpango-1.0-0 libcairo2 \
    libvulkan1 libxfixes3 libexpat1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ── Google Chrome stable ──────────────────────────────────────────────────────
RUN wget -q -O /tmp/chrome.deb \
    https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application + test source ─────────────────────────────────────────────────
COPY . .

# ── Entry point ───────────────────────────────────────────────────────────────
# The test container connects to the already-running app container via
# APP_URL env variable (injected by Jenkins). It does NOT start Flask itself.
CMD ["pytest", "test_taskflow.py", "-v", "--tb=short", \
     "--junit-xml=/app/test-results/results.xml"]
