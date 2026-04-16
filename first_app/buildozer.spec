[app]
title = Map2motion
package.name = map2motion
package.domain = com.map2motion
icon.filename = icon.png

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,xml
source.include_patterns = Assets/**,core/**,screens/**

version = 0.1


requirements = python3==3.11.9,kivy,kivymd,materialyoucolor,plyer,pyjnius,android,requests,pillow

orientation = portrait
android.allow_backup = True

android.permissions = INTERNET, CAMERA, READ_MEDIA_IMAGES, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, ACCESS_WIFI_STATE, ACCESS_NETWORK_STATE

android.api = 34
android.minapi = 24
android.sdk = 34
android.build_tools_ver = 34.0.0
android.ndk = 25b

android.archs = arm64-v8a

android.gradle_dependencies = androidx.core:core:1.7.0
android.enable_androidx = True

# Настройки для камеры
android.add_resources = res/xml/file_paths.xml:xml/file_paths.xml
android.manifest.queries = <intent><action android:name="android.media.action.IMAGE_CAPTURE" /></intent>
android.exported_activities = org.kivy.android.PythonActivity
p4a.branch = master
