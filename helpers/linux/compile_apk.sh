#!/usr/bin/env bash
#
# Build the klodTalk Android APK.
# Requires: ANDROID_HOME (or ANDROID_SDK_ROOT) set, Java 17+
#
# Usage:
#   ./helpers/linux/compile_apk.sh          # debug APK
#   ./helpers/linux/compile_apk.sh release  # release APK (unsigned)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_PROJECT="$PROJECT_ROOT/clients/android/KlodTalk"

BUILD_TYPE="${1:-debug}"

if [ -z "${ANDROID_HOME:-}" ] && [ -z "${ANDROID_SDK_ROOT:-}" ]; then
    echo "ERROR: ANDROID_HOME or ANDROID_SDK_ROOT must be set."
    echo "  export ANDROID_HOME=\$HOME/Android/Sdk"
    exit 1
fi

if ! command -v java &>/dev/null; then
    echo "ERROR: Java not found. Install JDK 17+."
    exit 1
fi

JAVA_VER=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VER" -lt 17 ] 2>/dev/null; then
    echo "WARNING: Java 17+ recommended. Detected version $JAVA_VER."
fi

cd "$ANDROID_PROJECT"

if [ ! -f gradlew ]; then
    echo "Gradle wrapper not found. Generating..."
    if command -v gradle &>/dev/null; then
        gradle wrapper --gradle-version 8.5
    else
        echo "ERROR: Neither gradlew nor gradle found."
        echo "  Install Gradle or open the project in Android Studio first."
        exit 1
    fi
fi

chmod +x gradlew

echo "========================================="
echo " Building klodTalk APK ($BUILD_TYPE)"
echo "========================================="

if [ "$BUILD_TYPE" = "release" ]; then
    ./gradlew assembleRelease
    APK_PATH="app/build/outputs/apk/release/app-release-unsigned.apk"
else
    ./gradlew assembleDebug
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
fi

if [ -f "$APK_PATH" ]; then
    DEST="$PROJECT_ROOT/build"
    mkdir -p "$DEST"
    cp "$APK_PATH" "$DEST/"
    APK_NAME=$(basename "$APK_PATH")
    echo ""
    echo "BUILD SUCCESSFUL"
    echo "APK copied to: build/$APK_NAME"
    echo "Full path: $DEST/$APK_NAME"
else
    echo ""
    echo "Build finished but APK not found at expected path."
    echo "Check the Gradle output above for errors."
    exit 1
fi
