#!/usr/bin/env python3
import base64
import functools
import http.server
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

def find_chrome():
    candidates = []
    if os.environ.get("CHROME_BIN"):
        candidates.append(os.environ["CHROME_BIN"])

    for command in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        resolved = shutil.which(command)
        if resolved:
            candidates.append(resolved)

    candidates.extend([
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        str(Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Google/Chrome/Application/chrome.exe"),
    ])

    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file():
            return path
    return None


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / ".tests-output"
PROFILE_DIR = OUTPUT_DIR / "chrome-profile"
LOG_FILE = OUTPUT_DIR / "chrome.log"
CHROME = find_chrome()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return


class CdpSocket:
    def __init__(self, url):
        parsed = urlparse(url)
        self.sock = socket.create_connection((parsed.hostname, parsed.port), timeout=5)
        self.buffer = b""
        self.next_id = 1
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {parsed.path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        self.sock.sendall(request)
        response = self._read_until(b"\r\n\r\n")
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"CDP WebSocket handshake failed: {response[:300]!r}")

    def _read_until(self, marker):
        while marker not in self.buffer:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("CDP socket closed during handshake")
            self.buffer += chunk
        end = self.buffer.index(marker) + len(marker)
        value, self.buffer = self.buffer[:end], self.buffer[end:]
        return value

    def _read_exact(self, size):
        while len(self.buffer) < size:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("CDP socket closed")
            self.buffer += chunk
        value, self.buffer = self.buffer[:size], self.buffer[size:]
        return value

    def _send_frame(self, payload, opcode=0x1):
        payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        mask = os.urandom(4)
        size = len(payload)
        header = bytearray([0x80 | opcode])
        if size < 126:
            header.append(0x80 | size)
        elif size < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", size))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", size))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def _receive_json(self):
        while True:
            first, second = self._read_exact(2)
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            size = second & 0x7F
            if size == 126:
                size = struct.unpack("!H", self._read_exact(2))[0]
            elif size == 127:
                size = struct.unpack("!Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else None
            payload = self._read_exact(size)
            if mask:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x8:
                raise ConnectionError("CDP WebSocket closed")
            if opcode == 0x9:
                self._send_frame(payload, opcode=0xA)
                continue
            if opcode == 0x1:
                return json.loads(payload.decode("utf-8"))

    def call(self, method, params=None):
        request_id = self.next_id
        self.next_id += 1
        self._send_frame(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = self._receive_json()
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"CDP {method} failed: {message['error']}")
                return message.get("result", {})

    def close(self):
        try:
            self._send_frame(b"", opcode=0x8)
        except OSError:
            pass
        self.sock.close()


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def get_json(url, timeout=1):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def wait_for_json(url, timeout=12):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            return get_json(url)
        except Exception as error:
            last_error = error
            time.sleep(0.1)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def target_socket(debug_port, target_id, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for target in get_json(f"http://127.0.0.1:{debug_port}/json/list"):
            if target.get("id") == target_id and target.get("webSocketDebuggerUrl"):
                return CdpSocket(target["webSocketDebuggerUrl"])
        time.sleep(0.1)
    raise RuntimeError(f"CDP target did not appear: {target_id}")


def evaluate_until(cdp, expression, predicate, timeout=8):
    deadline = time.time() + timeout
    last_value = None
    while time.time() < deadline:
        result = cdp.call("Runtime.evaluate", {"expression": expression, "returnByValue": True})
        if "exceptionDetails" not in result:
            last_value = result.get("result", {}).get("value")
            if predicate(last_value):
                return last_value
        time.sleep(0.1)
    raise RuntimeError(f"Browser assertion timed out. Last value: {last_value!r}")


def main():
    if CHROME is None:
        raise SystemExit("FAIL Chrome or Chromium executable not found. Set CHROME_BIN to its path.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(PROFILE_DIR, ignore_errors=True)

    handler = functools.partial(QuietHandler, directory=str(ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    fixture_url = f"http://127.0.0.1:{httpd.server_port}/tests/browser-fixture.html"

    debug_port = free_port()
    log_handle = LOG_FILE.open("w", encoding="utf-8")
    chrome_args = [
        str(CHROME),
        "--headless=new",
        "--disable-gpu",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={PROFILE_DIR}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-debugging-port={debug_port}",
        "about:blank",
    ]
    if sys.platform.startswith("linux"):
        chrome_args.insert(1, "--no-sandbox")

    process = subprocess.Popen(
        chrome_args,
        stdout=subprocess.DEVNULL,
        stderr=log_handle,
    )

    browser = None
    try:
        version = wait_for_json(f"http://127.0.0.1:{debug_port}/json/version")
        browser = CdpSocket(version["webSocketDebuggerUrl"])

        fixture_target = browser.call("Target.createTarget", {"url": fixture_url})["targetId"]
        fixture_page = target_socket(debug_port, fixture_target)
        fixture_result = evaluate_until(
            fixture_page,
            "({result: document.body.dataset.testResult, output: document.querySelector('#results')?.textContent || ''})",
            lambda value: isinstance(value, dict) and value.get("result") in {"PASS", "FAIL"},
        )
        fixture_page.close()

        if fixture_result["result"] != "PASS":
            raise RuntimeError(f"Real Chrome fixture failed:\n{fixture_result['output']}")
        if "PASS 17 checks" not in fixture_result["output"]:
            raise RuntimeError(f"Unexpected fixture output:\n{fixture_result['output']}")
        print("PASS real Chrome fixture: 17 DOM extraction, localization, local download, JSON and CSV checks")
    finally:
        if browser is not None:
            try:
                browser.call("Browser.close")
            except Exception:
                pass
            browser.close()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        log_handle.close()
        httpd.shutdown()
        httpd.server_close()
        shutil.rmtree(PROFILE_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
