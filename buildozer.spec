[app]

title = Map2motion
package.name = map2motion
package.domain = com.map2motion

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = Assets/**

version = 0.1

requirements = python3,kivy,kivymd,plyer,pyjnius,android

orientation = portrait

android.allow_backup = True

# Permissions
android.permissions = CAMERA,READ_MEDIA_IMAGES

# API
android.api = 33
android.minapi = 24

# Architecture
android.archs = arm64-v8a

# AndroidX (нужно для FileProvider)
android.gradle_dependencies = androidx.core:core:1.7.0

# Activity
android.exported_activities = org.kivy.android.PythonActivity

#android.add_resources = res

android.manifest.template = AndroidManifest.tmpl.xml

android.enable_androidx = True

android.res_xml = provider_paths.xml

#android.extra_manifest_application_arguments = extra_manifest.xml
