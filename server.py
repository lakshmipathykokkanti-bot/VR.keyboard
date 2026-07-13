from flask import Flask, render_template, send_file
from flask_socketio import SocketIO
import pyautogui
import qrcode
import socket
import os
import threading
import webbrowser

app = Flask(__name__)
app.config["SECRET_KEY"] = "remote-keyboard-secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# Safety feature
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01


def get_local_ip():
    """Get laptop's local network IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())
    finally:
        s.close()

    return ip


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/qr")
def qr_code():
    return send_file("keyboard_qr.png", mimetype="image/png")


@socketio.on("connect")
def connected():
    print("Phone connected")


@socketio.on("disconnect")
def disconnected():
    print("Phone disconnected")


@socketio.on("key")
def handle_key(data):
    key = str(data.get("key", ""))

    key_map = {
        "ESC": "esc",
        "TAB": "tab",
        "CAPS": "capslock",
        "ENTER": "enter",
        "BACKSPACE": "backspace",
        "DELETE": "delete",
        "INSERT": "insert",
        "HOME": "home",
        "END": "end",
        "PAGEUP": "pageup",
        "PAGEDOWN": "pagedown",
        "SPACE": "space",
        "UP": "up",
        "DOWN": "down",
        "LEFT": "left",
        "RIGHT": "right",
    }

    # Function keys
    if key.startswith("F") and key[1:].isdigit():
        number = int(key[1:])

        if 1 <= number <= 12:
            pyautogui.press(key.lower())
            return

    if key in key_map:
        pyautogui.press(key_map[key])
        return

    # Normal characters
    if len(key) == 1:
        pyautogui.write(key)


@socketio.on("shortcut")
def handle_shortcut(data):
    keys = data.get("keys", [])

    allowed = {
        "ctrl",
        "alt",
        "shift",
        "win",
        "a",
        "c",
        "v",
        "x",
        "z",
        "y",
        "s",
        "f",
        "t",
        "w",
        "n",
        "p",
        "enter",
        "tab",
        "esc",
        "delete",
        "backspace",
        "left",
        "right",
        "up",
        "down",
    }

    clean_keys = [
        str(key).lower()
        for key in keys
        if str(key).lower() in allowed
    ]

    if clean_keys:
        pyautogui.hotkey(*clean_keys)


if __name__ == "__main__":

    ip = get_local_ip()
    port = 5000

    url = f"http://{ip}:{port}"

    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    image.save("keyboard_qr.png")

    print("\n==============================")
    print("REMOTE PHONE KEYBOARD")
    print("==============================")
    print(f"Phone URL: {url}")
    print("QR saved as: keyboard_qr.png")
    print("==============================\n")

    # Open QR in browser
    threading.Timer(
        1.5,
        lambda: webbrowser.open(f"http://127.0.0.1:{port}/qr")
    ).start()

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )