[app]

# (str) Title of your application
title = Map2motion

# (str) Package name
package.name = map2motion

# (str) Package domain (needed for android/ios packaging)
package.domain = com.map2motion

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) List of inclusions using pattern matching
source.include_patterns = Assets/**

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
# Do not prefix with './'
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,plyer,pyjnius,android

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
orientation = portrait

android.allow_backup = True

# Permissions
android.permissions = CAMERA,READ_MEDIA_IMAGES

# API levels
android.api = 33
android.minapi = 24

# Architecture
android.archs = arm64-v8a

# Gradle dependencies
android.gradle_dependencies = androidx.core:core:1.7.0

# Main exported activity
android.exported_activities = org.kivy.android.PythonActivity

android.extra_manifest_xml = extra_manifest.xml
android.add_resources = provider_paths.xml:xml/provider_paths.xml

android:authorities="${applicationId}.provider"
