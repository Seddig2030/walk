[app]
title = WalkLearn
package.name = walklearn
package.domain = org.walklearn
source.dir = .
source.include_exts = py,json,ttf,png,svg
version = 4.0.0
requirements = python3,kivy==2.3.0,pyjnius,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png

# Pins python-for-android itself to the release that shipped alongside
# Kivy 2.3.0 and still defaults to building Python 3.11 for the device.
# Newer p4a checkouts default to Python 3.14, which Kivy 2.3.0's C code
# does not compile against yet. Without this, buildozer clones p4a's
# latest master branch regardless of any pip-installed p4a version.
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.permissions = INTERNET
