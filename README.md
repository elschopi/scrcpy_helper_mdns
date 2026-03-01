# ADB Wireless Connector with mDNS Discovery

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-blue.svg)](https://www.microsoft.com/windows)

A streamlined tool for automatically discovering and connecting to Android devices over WiFi using mDNS (Bonjour/Zeroconf), with integrated pairing support and scrcpy launcher.

## ✨ Features

- 🔍 **Automatic Device Discovery** - No need to manually enter IP addresses
- 🔐 **Integrated Pairing** - Supports both QR code and pairing code methods
- 🚀 **One-Click Connection** - Discovers, pairs (if needed), and launches scrcpy automatically
- 🧹 **Optimized Performance** - Aggressive cleanup prevents system lag and mouse issues
- 📱 **Multi-Device Support** - Automatically detects and lets you choose from multiple devices
- 💻 **Portable** - Single executable with no installation required

## 📋 Requirements

### System Requirements
- **OS**: Windows 10/11 (primary), Linux/macOS (with modifications)
- **Network**: PC and Android device on same WiFi network
- **Android**: Android 11+ with Wireless Debugging enabled

### Dependencies
- **Python** 3.7+ (for running from source)
- **zeroconf** - mDNS service discovery
- **qrcode** (optional) - QR code display for pairing
- **scrcpy** - Screen mirroring tool ([Download](https://github.com/Genymobile/scrcpy))
- **ADB** - Android Debug Bridge ([Download](https://developer.android.com/tools/releases/platform-tools))

## 🚀 Quick Start

### Option 1: Pre-built Executable (Recommended)

1. **Download** the latest release from [Releases](https://github.com/elschopi/scrcpy_helper_mdns/releases)
2. **Extract** the ZIP file to a folder
3. **Download scrcpy** and place `scrcpy.exe` in the same folder
4. **Run** `connector_mdns.exe`

### Option 2: Run from Source

```bash
# Install dependencies
pip install zeroconf qrcode

# Run the script
python connector_mdns.py
```

**Note**: Ensure `scrcpy.exe` is in the same directory or `adb` is in your PATH.

## 📱 Android Setup

1. **Enable Developer Options**:
   - Go to `Settings` → `About Phone`
   - Tap `Build Number` 7 times

2. **Enable Wireless Debugging**:
   - Go to `Settings` → `Developer Options`
   - Enable `Wireless Debugging`
   - Ensure device is on the same WiFi as your PC

3. **First-time Pairing** (if prompted):
   - Choose pairing method in the tool
   - Follow on-screen instructions

## 🎯 Usage

1. **Launch the tool**:
   ```bash
   connector_mdns.exe
   ```

2. **Automatic Discovery**:
   - Tool scans for devices (5 seconds)
   - Select device if multiple found

3. **Pairing** (if needed):
   - **Option 1**: Enter 6-digit pairing code from phone
   - **Option 2**: Scan QR code displayed in terminal

4. **Enjoy scrcpy**:
   - Screen mirroring starts automatically
   - Device screen turns off to save battery
   - Close window or press `Alt+F4` to exit

## 🔧 Configuration

Edit these constants in `connector_mdns.py` to customize behavior:

```python
DISCOVERY_TIMEOUT = 5       # Device discovery duration (seconds)
PAIRING_TIMEOUT = 30        # Pairing wait time (seconds)
```

### Scrcpy Parameters

Default scrcpy settings (modify in `state_launch` method):

```python
--max-size=1280           # Resolution limit
--turn-screen-off         # Turn off device screen
--keyboard=uhid           # Keyboard input method
```

Additional options you can add:
- `--bit-rate=8M` - Video bitrate
- `--max-fps=60` - Frame rate limit
- `--no-audio` - Disable audio streaming
- `--stay-awake` - Keep device awake
- `--show-touches` - Show touch indicators
- `--mouse=uhid` - Mouse input method

See [scrcpy documentation](https://github.com/Genymobile/scrcpy) for all options.

## 🛠️ Building from Source

### Build Executable with PyInstaller

```bash
# Install build dependencies
pip install pyinstaller zeroconf qrcode

# Build executable
pyinstaller --onefile --console --name connector_mdns connector_mdns.py

# Output will be in dist/connector_mdns.exe
```

### Advanced Build Options

```bash
# With custom icon
pyinstaller --onefile --console --icon=icon.ico --name connector_mdns connector_mdns.py

# Optimized size
pyinstaller --onefile --console --strip --name connector_mdns connector_mdns.py
```

## 🔥 Windows Firewall Setup

For mDNS discovery to work, allow UDP port 5353:

### Method 1: GUI
1. Open `Windows Defender Firewall` → `Advanced settings`
2. `Inbound Rules` → `New Rule`
3. Select `Port` → `UDP` → Port `5353`
4. Allow the connection → Apply to all profiles
5. Name it "mDNS"

### Method 2: Command Line (Run as Administrator)
```cmd
netsh advfirewall firewall add rule name="mDNS" dir=in action=allow protocol=UDP localport=5353
```

## 🐛 Troubleshooting

### No devices found
- ✅ Verify both devices are on same WiFi
- ✅ Check "Wireless Debugging" is enabled on Android
- ✅ Set Windows network profile to "Private"
- ✅ Ensure firewall allows UDP port 5353
- ✅ Disable VPN if active

### Connection fails
- ✅ Device may need pairing - follow prompts
- ✅ Restart "Wireless Debugging" on Android
- ✅ Run `adb kill-server` and try again

### Pairing fails
- ✅ Keep pairing screen open on Android
- ✅ Try alternative pairing method
- ✅ Verify code is entered correctly
- ✅ Restart "Wireless Debugging"

### scrcpy.exe not found
- ✅ Download scrcpy from [official releases](https://github.com/Genymobile/scrcpy/releases)
- ✅ Place `scrcpy.exe` in same folder as connector
- ✅ Ensure all scrcpy DLLs are present

### QR code not displaying
- ✅ Install qrcode: `pip install qrcode`
- ✅ Use pairing code method instead

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/elschopi/scrcpy_helper_mdns/blob/main/LICENSE) file for details.

## 🙏 Acknowledgments

- **[scrcpy](https://github.com/Genymobile/scrcpy)** - Excellent screen mirroring tool by Genymobile
- **[zeroconf](https://github.com/python-zeroconf/python-zeroconf)** - Pure Python mDNS implementation
- **[qrcode](https://github.com/lincolnloop/python-qrcode)** - QR code generation library
- **Android Debug Bridge (ADB)** - Part of Android SDK Platform Tools

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/elschopi/scrcpy_helper_mdns/issues)

## ⭐ Star History

If you find this tool useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the Android development community**
