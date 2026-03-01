#!/usr/bin/env python3
"""
ADB Wireless Connector with mDNS Discovery and QR Pairing
Cross-platform version with aggressive Zeroconf cleanup to prevent system lag
"""

import subprocess
import time
import os
import sys
import socket
import random
import gc
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf, IPVersion

# ====
# CONFIGURATION
# ====

DISCOVERY_TIMEOUT = 5       # Seconds to scan for devices
PAIRING_TIMEOUT = 30        # Seconds to wait for pairing service
CONNECT_TYPE = "_adb-tls-connect._tcp.local."
PAIR_TYPE = "_adb-tls-pairing._tcp.local."

# ====
# PATH SETUP
# ====

if getattr(sys, "frozen", False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Platform-specific executable names
if sys.platform == "win32":
    SCRCPY_PATH = os.path.join(SCRIPT_DIR, "scrcpy.exe")
    ADB_PATH = os.path.join(SCRIPT_DIR, "adb.exe")
else:
    SCRCPY_PATH = os.path.join(SCRIPT_DIR, "scrcpy")
    ADB_PATH = os.path.join(SCRIPT_DIR, "adb")

if not os.path.exists(ADB_PATH):
    ADB_PATH = "adb"

# ====
# ADB HELPERS
# ====

def run_adb(args):
    """Run adb command and return combined stdout/stderr."""
    try:
        res = subprocess.run(
            [ADB_PATH] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return (res.stdout or "") + (res.stderr or "")
    except Exception as e:
        return f"Error: {e}"

def adb_is_paired(serial):
    """Check if device is in adb's trust database."""
    out = run_adb(["devices"])
    for line in out.splitlines():
        if serial in line and ("device" in line or "offline" in line):
            return True
    return False

def adb_connect(ip, port):
    """Attempt to connect to device."""
    target = f"{ip}:{port}"
    out = run_adb(["connect", target])
    return target, out

def adb_pair(ip, port, code):
    """Attempt to pair with device using pairing code."""
    target = f"{ip}:{port}"
    out = run_adb(["pair", target, code])
    success = "successfully paired" in out.lower()
    return success, out

# ====
# mDNS DISCOVERY (with aggressive cleanup)
# ====

class ADBServiceListener(ServiceListener):
    """Listener for ADB mDNS services."""

    def __init__(self):
        self.devices = []

    def add_service(self, zc, type_, name):
        info = zc.get_service_info(type_, name)
        if info:
            try:
                ip = socket.inet_ntoa(info.addresses[0])
                port = info.port
                device_id = name.split(".")[0]

                item = {"id": device_id, "ip": ip, "port": port}
                if item not in self.devices:
                    self.devices.append(item)
                    print(f"  ✓ {ip}:{port}")
            except Exception:
                pass

    def remove_service(self, zc, type_, name):
        pass

    def update_service(self, zc, type_, name):
        pass

def discover_services(service_type, timeout):
    """
    Discover ADB services via mDNS with AGGRESSIVE cleanup.
    This prevents background threads from causing system lag.
    """
    zc = None
    browser = None
    listener = None

    try:
        # IPv4 only to reduce multicast noise on Windows
        zc = Zeroconf(ip_version=IPVersion.V4Only)
        listener = ADBServiceListener()
        browser = ServiceBrowser(zc, service_type, listener)

        # Discovery window
        time.sleep(timeout)

        # CRITICAL: Explicit shutdown sequence
        # This prevents threads from lingering and causing mouse lag
        if browser:
            browser.cancel()

        if zc:
            zc.close()

        # Give system time to tear down sockets and threads
        time.sleep(0.5)

        # Extract results before cleanup
        devices = listener.devices.copy() if listener else []

        # Force cleanup
        del browser
        del listener
        del zc

        # Aggressive garbage collection to ensure thread cleanup
        gc.collect()

        return devices

    except Exception as e:
        print(f"  ⚠️  Discovery error: {e}")

        # Emergency cleanup
        try:
            if browser:
                browser.cancel()
        except:
            pass

        try:
            if zc:
                zc.close()
        except:
            pass

        gc.collect()
        return []

# ====
# QR CODE DISPLAY
# ====

def display_qr_code(text):
    """Display QR code in terminal (requires qrcode package)."""
    try:
        import qrcode
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(text)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        return True
    except ImportError:
        print("\n[!] QR-Code display not available.")
        print("    Install 'qrcode': pip install qrcode")
        return False

# ====
# CROSS-PLATFORM HOSTNAME
# ====

def get_hostname():
    """Get the computer's hostname in a cross-platform way."""
    try:
        # socket.gethostname() works on Windows, Linux, and macOS
        hostname = socket.gethostname()
        if hostname:
            return hostname
    except Exception:
        pass

    # Fallback: try environment variables
    # Windows: COMPUTERNAME
    # Unix/Linux/macOS: HOSTNAME or HOST
    for env_var in ["COMPUTERNAME", "HOSTNAME", "HOST"]:
        hostname = os.environ.get(env_var)
        if hostname:
            return hostname

    # Final fallback
    return "PC-Connector"

# ====
# STATE MACHINE
# ====

class ConnectionStateMachine:
    """Manages the connection flow: DISCOVER → CONNECT → VERIFY → PAIR → LAUNCH"""

    def __init__(self):
        self.selected_device = None
        self.target_serial = None

    def run(self):
        """Execute the full connection flow."""
        print("=" * 60)
        print("ADB Wireless Connector")
        print("=" * 60)

        # STATE 1: DISCOVER
        if not self.state_discover():
            return False

        # STATE 2: CONNECT
        if not self.state_connect():
            return False

        # STATE 3: VERIFY
        if not self.state_verify():
            # STATE 4: PAIR (if needed)
            if not self.state_pair():
                return False
            # Retry connect after pairing
            if not self.state_connect():
                return False

        # Final cleanup before launching scrcpy
        print("\n[Cleanup] Shutting down mDNS services...")
        gc.collect()
        time.sleep(0.3)

        # STATE 5: LAUNCH
        return self.state_launch()

    def state_discover(self):
        """STATE 1: Discover devices via mDNS."""
        print(f"\n[1/5] Searching for devices ({DISCOVERY_TIMEOUT}s)...")
        devices = discover_services(CONNECT_TYPE, DISCOVERY_TIMEOUT)

        if not devices:
            print("\n❌ No devices found.")
            print("\nTroubleshooting:")
            print("  • Is 'Wireless Debugging' enabled on your phone?")
            print("  • Are PC and phone on the same network?")
            print("  • Windows: Network profile set to 'Private'?")
            print("  • Windows: Firewall allows UDP port 5353?")
            return False

        # Select device
        if len(devices) > 1:
            print(f"\n{len(devices)} devices found:")
            for i, d in enumerate(devices, 1):
                print(f"  [{i}] {d['ip']}:{d['port']}")

            while True:
                try:
                    choice = int(input("\nSelect device (number): "))
                    if 1 <= choice <= len(devices):
                        self.selected_device = devices[choice - 1]
                        break
                except (ValueError, KeyboardInterrupt):
                    pass
                print("Invalid selection.")
        else:
            self.selected_device = devices[0]
            print(f"  → {self.selected_device['ip']}:{self.selected_device['port']}")

        self.target_serial = f"{self.selected_device['ip']}:{self.selected_device['port']}"
        return True

    def state_connect(self):
        """STATE 2: Attempt ADB connection."""
        print(f"\n[2/5] Connecting to {self.target_serial}...")
        target, out = adb_connect(self.selected_device['ip'], self.selected_device['port'])
        print(f"  {out.strip()}")
        return True  # Always continue to verify

    def state_verify(self):
        """STATE 3: Verify device is paired and known to ADB."""
        print(f"\n[3/5] Checking pairing status...")

        if adb_is_paired(self.target_serial):
            print("  ✅ Device is paired and connected.")
            return True
        else:
            print("  ⚠️  Device is NOT paired.")
            return False

    def state_pair(self):
        """STATE 4: Pair device using pairing code or QR."""
        print(f"\n[4/5] Pairing required...")
        print("\nPairing methods:")
        print("  [1] Pairing code (recommended)")
        print("  [2] QR code displayed on PC")

        mode = input("\nSelect 1 or 2: ").strip()

        if mode == "2":
            result = self._pair_via_qr()
        else:
            result = self._pair_via_code()

        # Cleanup after pairing
        gc.collect()
        time.sleep(0.3)

        return result

    def _pair_via_code(self):
        """Pair using 6-digit pairing code."""
        print("\n📱 On your phone:")
        print("   [Wireless Debugging] → [Pair device with pairing code]")
        print("\n   A 6-digit code and port will be displayed.")

        code = input("\n   Enter the 6-digit code: ").strip()

        if not code or len(code) != 6:
            print("❌ Invalid code.")
            return False

        print(f"\n   Searching for pairing service (5s)...")
        pair_devices = discover_services(PAIR_TYPE, 5)

        if not pair_devices:
            print("❌ Pairing service not found.")
            print("   Is the pairing screen still open on your phone?")
            return False

        # Find pairing service for our device's IP
        pair_target = None
        for d in pair_devices:
            if d['ip'] == self.selected_device['ip']:
                pair_target = d
                break

        if not pair_target:
            pair_target = pair_devices[0]

        print(f"   → Pairing with {pair_target['ip']}:{pair_target['port']}...")
        success, out = adb_pair(pair_target['ip'], pair_target['port'], code)
        print(f"   {out.strip()}")

        if success:
            print("   ✅ Pairing successful!")
            return True
        else:
            print("   ❌ Pairing failed.")
            return False

    def _pair_via_qr(self):
        """Pair using QR code displayed on PC."""
        print("\n📱 On your phone:")
        print("   [Wireless Debugging] → [Pair device with QR code]")

        name = get_hostname()
        passwd = f"{random.randint(0, 999999):06d}"
        qr_text = f"WIFI:T:ADB;S:{name};P:{passwd};;"

        print("\n   Scan this QR code:\n")

        if not display_qr_code(qr_text):
            print("\n   Fallback: Use pairing code instead.")
            return self._pair_via_code()

        print(f"\n   Searching for pairing service (10s)...")
        pair_devices = discover_services(PAIR_TYPE, 10)

        if not pair_devices:
            print("❌ Pairing service not found.")
            return False

        pair_target = None
        for d in pair_devices:
            if d['ip'] == self.selected_device['ip']:
                pair_target = d
                break

        if not pair_target:
            pair_target = pair_devices[0]

        print(f"   → Pairing with {pair_target['ip']}:{pair_target['port']}...")
        success, out = adb_pair(pair_target['ip'], pair_target['port'], passwd)
        print(f"   {out.strip()}")

        if success:
            print("   ✅ Pairing successful!")
            return True
        else:
            print("   ❌ Pairing failed.")
            return False

    def state_launch(self):
        """STATE 5: Launch scrcpy."""
        print(f"\n[5/5] Starting scrcpy...")

        if not os.path.exists(SCRCPY_PATH):
            print(f"\n❌ scrcpy not found: {SCRCPY_PATH}")
            print("   Make sure scrcpy is in the same folder.")
            return False

        print(f"   Target: {self.target_serial}")
        print("   Parameters: --max-size=1280 --turn-screen-off --keyboard=uhid")
        print("   To exit: Alt (left) + F4 or close window\n")

        try:
            subprocess.run([
                SCRCPY_PATH,
                "--max-size=1280",
                "--turn-screen-off",
                f"--tcpip={self.target_serial}",
                "--keyboard=uhid"
            ])
            print("\n✅ scrcpy closed.")
            return True
        except Exception as e:
            print(f"\n❌ Error starting scrcpy: {e}")
            return False

# ====
# MAIN ENTRY POINT
# ====

def main():
    try:
        sm = ConnectionStateMachine()
        success = sm.run()

        if not success:
            print("\n❌ Connection failed.")
            time.sleep(5)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user.")
        # Emergency cleanup
        gc.collect()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(10)
        sys.exit(1)
    finally:
        # Final cleanup on exit
        print("\n[Cleanup] Cleaning up...")
        gc.collect()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
    print("\nDone.")
    time.sleep(2)
