[app]
title = MealCare
package.name = planner
package.domain = org.mealcare

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,atlas,ttf,md
source.exclude_dirs = .git,.venv,venv,__pycache__,tests,build,.buildozer

version = 1.0.0

# IMPORTANT: Kivy needs sdl2 backend + android module for services
requirements = python3,kivy==2.3.1,plyer,android,pyjnius,sdl2_ttf

# Presplash / icon (make sure these exist, or remove the lines)
# icon.filename = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

orientation = portrait
fullscreen = 0

# Service — "sticky" is NOT a valid flag. Use "foreground" or omit.
services = reminder:service.py:foreground

android.permissions = INTERNET,POST_NOTIFICATIONS,VIBRATE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE
android.features = android.hardware.telephony

android.api = 34
android.minapi = 26
android.ndk = 27.0.12077973
android.archs = arm64-v8a, armeabi-v7a

android.private_storage = True
android.accept_sdk_license = True

# Use APK for sideloading; AAB is only for Google Play upload.
android.release_artifact = apk
android.debug_artifact   = apk

# Signing (create keystore once — see step 5)
# android.keystore = %(source.dir)s/mealcare.keystore
# android.keyalias = mealcare
# android.keystore_password = YOUR_PASSWORD
# android.key_password = YOUR_PASSWORD

p4a.branch = master
log_level = 2
warn_on_root = 1
SPEC
