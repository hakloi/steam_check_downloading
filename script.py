# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import winreg
from pathlib import Path
import re
import time

SPEED_RE = re.compile(r"([0-9.]+)\s*(MB|KB)/s", re.IGNORECASE)
APPID_RE = re.compile(r"AppID\s+(\d+)", re.IGNORECASE)
RATE_RE = re.compile(
    r"Current download rate:\s*([0-9.]+)\s*Mbps",
    re.IGNORECASE
)


"""
Searches for Steam installation and return Steam's path in OS
"""
def get_steam_installation_path():
    try:
        with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Valve\Steam"
        ) as key:
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            path = Path(steam_path)

            if path.exists():
                return path
            else:
                raise RuntimeError(f"Steam path found in registry but doesn't exist: {steam_path}\n")

    except FileNotFoundError:
        raise RuntimeError("Steam installation not found in Windows registry\n")

"""
Searches for content_log.txt in stream's path
"""
def read_content_log(steam_path):
    log_path = steam_path / "logs" / "content_log.txt"

    if not log_path.exists():
        print("content_log.txt not found")
        return

    print("Last 10 lines of content_log.txt:\n")
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.strip())

        print()

"""
Extracts data
"""
def parse_current_download_rate(steam_path):
    log_path = steam_path / "logs" / "content_log.txt"

    if not log_path.exists():
        return None

    with open(log_path, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for line in reversed(lines[-200:]):
        match = RATE_RE.search(line)
        if match:
            return float(match.group(1))

    return None

def find_downloading_game(steam_path):
    steamapps_path = steam_path / "steamapps"

    if not steamapps_path.exists():
        return None

    for manifest in steamapps_path.glob("appmanifest_*.acf"):
        content = manifest.read_text(encoding="utf-8", errors="ignore")

        name_match = re.search(r'"name"\s+"(.+)"', content)
        state_match = re.search(r'"StateFlags"\s+"(\d+)"', content)

        if not name_match or not state_match:
            continue

        name = name_match.group(1)
        state = int(state_match.group(1))

        if state != 4:
            return name

    return None

def get_download_status(steam_path):
    rate = parse_current_download_rate(steam_path)
    game = find_downloading_game(steam_path)

    if rate is None:
        return "NO_DATA", game, rate

    if rate == 0:
        return "PAUSED", game, rate

    return "DOWNLOADING", game, rate


def monitor_downloads(steam_path, minutes):
    for i in range(minutes):
        status, game, rate = get_download_status(steam_path)

        if status == "DOWNLOADING":
            print(f"[{i+1}] ⬇ {game}: {rate} Mbps")
        elif status == "PAUSED":
            print(f"[{i+1}] ⏸ {game or 'No active game'}")
        else:
            print(f"[{i+1}] ℹ No download activity")

        time.sleep(60)

def run(mode):
    steam_path = get_steam_installation_path()

    if mode == "once":
        monitor_downloads(steam_path, 1)

    elif mode == "five":
        monitor_downloads(steam_path, 5)

    elif mode == "continuous":
        print("Continuous monitoring started (Ctrl+C to stop)")
        while True:
            monitor_downloads(steam_path, 1)


if __name__ == '__main__':
    mode = input("Choose mode (once / five / continuous): ").strip().lower()
    if mode not in {"once", "five", "continuous"}:
        mode = "five"

    run(mode)
