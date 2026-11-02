[app]
title = SEF - The Adventurer
package.name = sefadventurer
package.domain = org.sef
source.dir = .
source.include_exts = py,png,jpg,jpeg,json,ttf,wav,ogg,mp3
version = 1.0

requirements = python3,pygame,sdl2,sdl2_image,sdl2_mixer,sdl2_ttf

orientation = landscape
fullscreen = 1

android.archs = arm64-v8a
android.api = 33
android.minapi = 24
android.accept_sdk_license = True
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 0