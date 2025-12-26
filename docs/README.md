# PDF Scanner Android App

A production-ready Android document scanner app built with Python/Kivy and Buildozer.

## Features

- 📷 **Camera Scanning** - Live document edge detection with auto-crop
- ✂️ **Manual Crop** - Draggable corner adjustment for precise cropping  
- 🎨 **Image Filters** - B/W, Grayscale, Enhanced, Original
- 📄 **PDF Export** - Convert scans to PDF with compression presets
- 📁 **PDF Tools** - Merge, split PDFs
- 📖 **PDF Viewer** - In-app PDF viewing with zoom/pan
- ✏️ **Annotations** - Highlight, underline, strikeout, pen/ink
- 🖤 **Redaction** - Black or whiteout rectangles for privacy
- 📝 **Add Text** - Place text boxes on PDF pages
- ✍️ **Signatures** - Draw and place signatures
- 📂 **Open With** - Open PDFs from file manager
- 🔒 **Privacy First** - EXIF metadata stripping
- 💰 **Monetization** - AdMob + Remove Ads IAP

## PDF "Editing" Explained

> **Important:** This app provides annotation and overlay-based editing, not true PDF text editing.

| Tool | What It Does |
|------|--------------|
| Highlight | Yellow overlay rectangle |
| Underline | Line below selected area |
| Strikeout | Line through selected area |
| Pen/Ink | Freehand drawing |
| Redact Black | Black rectangle (covers content) |
| Redact White | White rectangle (whiteout) |
| Add Text | New text box overlay |
| Signature | Drawn signature image |

**Not supported:** Editing existing PDF text content directly.

## Prerequisites

### For WSL2 / Linux

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3 python3-pip python3-venv \
    openjdk-17-jdk \
    git zip unzip \
    build-essential libffi-dev libssl-dev \
    autoconf automake libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libglib2.0-dev

# Install Buildozer and Cython
pip3 install --user buildozer cython==0.29.36

# Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Android SDK Setup

Buildozer will auto-download SDK/NDK on first build. To pre-install:

```bash
# Set environment (optional)
export ANDROIDSDK="$HOME/.buildozer/android/platform/android-sdk"
export ANDROIDNDK="$HOME/.buildozer/android/platform/android-ndk-r25b"
```

## Project Structure

```
pdf_scanner_app/
├── main.py                 # App entry point
├── buildozer.spec          # Buildozer configuration
├── requirements.txt        # Python dependencies
├── app/
│   ├── domain/             # Business logic & models
│   ├── infra/              # Infrastructure (storage, imaging, PDF)
│   ├── ui/                 # Kivy screens & widgets
│   └── android_bridge/     # PyJNIus wrappers
├── android/
│   └── src/                # Java native code (AdMob, Billing)
├── assets/
│   ├── icons/              # App icons
│   └── images/             # UI images
└── docs/                   # Documentation
```

## Build Commands

### Debug Build

```bash
cd pdf_scanner_app
buildozer android debug
```

Output: `bin/pdfscanner-1.0.0-debug.apk`

### Release Build

```bash
# First time: create keystore
keytool -genkey -v -keystore ~/my-release-key.jks \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -alias pdf-scanner

# Build release
buildozer android release

# Sign APK
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
    -keystore ~/my-release-key.jks \
    bin/pdfscanner-1.0.0-release-unsigned.apk \
    pdf-scanner

# Align APK
zipalign -v 4 \
    bin/pdfscanner-1.0.0-release-unsigned.apk \
    bin/pdfscanner-1.0.0-release.apk
```

### Install to Device

```bash
adb install -r bin/pdfscanner-1.0.0-debug.apk
```

### View Logs

```bash
adb logcat | grep -E "python|kivy|PDFScanner"
```

## Configuration

### Before Release

1. **Update `buildozer.spec`:**
   - Replace `ca-app-pub-XXX` with your AdMob App ID
   - Update version number

2. **Update `AdMobManager.java`:**
   - Replace test ad unit IDs with production IDs

3. **Update `BillingManager.java`:**
   - Replace `remove_ads` SKU if using different product ID

4. **Create app icons:**
   - Place icon files in `assets/icons/`
   - Recommended: 512x512 PNG

5. **Update `settings.py`:**
   - Replace privacy policy URL

## Permissions

| Permission | Purpose |
|------------|---------|
| CAMERA | Document scanning |
| INTERNET | AdMob ads |
| ACCESS_NETWORK_STATE | Ad loading check |

## Architecture

- **UI Layer**: Kivy screens with Material Design 3 theme
- **Domain Layer**: Use cases, models, business logic
- **Infrastructure**: SQLite storage, image processing, PDF operations
- **Android Bridge**: PyJNIus wrappers for native functionality

## Troubleshooting

### Build Fails with Recipe Error

```bash
# Clean and rebuild
buildozer android clean
buildozer android debug
```

### Missing Gradle Dependencies

Ensure `buildozer.spec` has:
```ini
android.gradle_dependencies = com.google.android.gms:play-services-ads:23.0.0
android.enable_androidx = True
```

### Camera Not Working

- Check permission flow in `scanner.py`
- Verify `CAMERA` in `android.permissions`

### AdMob Not Loading

- Check AdMob App ID in `buildozer.spec` meta-data
- Verify ad unit IDs in `AdMobManager.java`
- Test with test ad IDs first

## License

Proprietary - All Rights Reserved

## Support

For issues, check `TESTING_MATRIX.md` for expected behaviors.
