#!/usr/bin/env bash
set -euo pipefail
mkdir -p preuves/mobile
apk=mobile/build/app/outputs/flutter-apk/app-debug.apk
test -s "$apk"
adb wait-for-device
adb install -r "$apk" | tee preuves/mobile/install.log
aapt=$(find "$ANDROID_HOME/build-tools" -type f -name aapt | sort -V | tail -1)
package=$("$aapt" dump badging "$apk" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -1)
echo "$package" > preuves/mobile/package.txt
adb shell monkey -p "$package" -c android.intent.category.LAUNCHER 1 | tee preuves/mobile/launch.log
sleep 35
adb exec-out screencap -p > preuves/mobile/flutter_login.png
adb shell input swipe 480 1450 480 700 500
sleep 3
adb exec-out screencap -p > preuves/mobile/flutter_apres_defilement.png
adb logcat -d -t 250 > preuves/mobile/logcat.log || true
