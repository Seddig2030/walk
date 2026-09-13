[app]
title = WalkLearn
package.name = walklearn
package.domain = org.walklearn
source.dir = .
source.include_exts = py,json,ttf,png,svg
version = 4.0.0
requirements = python3,kivy,pyjnius,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png

# Pin python-for-android to a known-stable release instead of master.
# This avoids picking up half-tested changes that can produce an APK
# which "builds successfully" but Android refuses to install.
p4a.branch = release-2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True
android.permissions = INTERNET
