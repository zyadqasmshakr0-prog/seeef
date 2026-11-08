[app]

title = SEF - The Adventurer
package.name = sefadventurer
package.domain = org.sef

source.dir = .
source.include_exts = py,png,jpg,jpeg,json,ttf,wav,ogg,mp3
source.exclude_dirs = tests,bin,.github,p4a-recipes

version = 1.0

# تثبيت Python وHost Python على الإصدار نفسه
requirements = python3==3.10.12,hostpython3==3.10.12,pygame,six,arabic-reshaper==3.0.0,python-bidi==0.4.2

orientation = landscape
fullscreen = 1

android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.ant_path = /usr/share/ant
p4a.bootstrap = sdl2

# استخدام إصدار رسمي محدد من python-for-android
p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 0