[app]
title = RelayControl
package.name = relaycontrol
package.domain = com.relaycontrol
icon.filename = icon.png

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml

source.include_patterns = Assets/**

version = 0.1


requirements = python3, kivy, kivymd, requests

orientation = portrait
android.allow_backup = True

android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE

android.minapi = 21
android.build_tools_ver = 34.0.0
android.ndk = 25b
android.api = 33

android.archs = arm64-v8a

android.gradle_dependencies = androidx.core:core:1.7.0
android.enable_androidx = True

android.exported_activities = org.kivy.android.PythonActivity
p4a.branch = master
