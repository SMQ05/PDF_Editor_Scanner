[app]

# (str) Title of your application
title = PDF Scanner

# (str) Package name
package.name = docscanner

# (str) Package domain (needed for android/ios packaging)
package.domain = com.pdfscanner

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,ttf,xml

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,app/*,android/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .git, __pycache__, docs

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# NOTE: Removed 'android' - it's auto-provided by python-for-android
requirements = python3,kivy==2.3.0,pillow,pypdf,pyjnius,plyer,certifi

# (str) Custom source folders for requirements
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/images/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icons/icon.png

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
android.presplash_color = #FFFFFF

# (list) Permissions
# - READ_MEDIA_IMAGES for Android 13+ gallery import
# - READ_EXTERNAL_STORAGE for legacy devices (ignored on 33+)
# - BILLING for IAP
android.permissions = CAMERA,INTERNET,ACCESS_NETWORK_STATE,READ_MEDIA_IMAGES,READ_EXTERNAL_STORAGE,com.android.vending.BILLING

# (int) Target Android API - Updated to 35 for Play Store compliance
android.api = 35

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use (optional)
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (str) Extra xml to write directly inside the <manifest> element of AndroidManifest.xml
# android.extra_manifest_xml = 

# (str) Extra xml to write directly inside the <application> element of AndroidManifest.xml
# Removed android:usesCleartextTraffic - not needed for AdMob/HTTPS
# android.extra_manifest_application_arguments = 

# (list) Copy these files to src/main/res/xml/ (used for file sharing permissions)
android.res_xml = android/res/xml/file_paths.xml

# (list) Android application meta-data to set (key=value format)
android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY

# (list) Android library project to add
#android.library_references =

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (list) Gradle dependencies
# NOTE: Removed explicit androidx.core - brought in by other deps
android.gradle_dependencies = com.google.android.gms:play-services-ads:23.0.0,com.android.billingclient:billing:6.1.0,com.tom_roush:pdfbox-android:2.0.27.0

# (bool) Enable AndroidX support
android.enable_androidx = True

# (list) Gradle repositories to add
android.gradle_repositories = google(),mavenCentral()

# (list) Java files to add to the android project
android.add_src = android/src

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

# (str) Custom AndroidManifest.xml template
# This is copied to p4a templates by hook.py before build
android.manifest = android/AndroidManifest.tmpl.xml

# (str) p4a build hook for automated manifest and Gradle patching
# The hook copies AndroidManifest.tmpl.xml and patches build.gradle for PDFBox
p4a.hook = hook.py

# (str) Extra arguments to pass to p4a
#p4a.extra_args =

#
# BUILD SYSTEM NOTES:
#
# Manifest injection is handled by hook.py which:
# 1. Copies android/AndroidManifest.tmpl.xml to p4a templates
# 2. Patches build.gradle with packagingOptions for PDFBox META-INF conflicts
#
# The manifest includes:
# - PythonActivity as LAUNCHER with singleTask
# - PdfOpenActivity with VIEW intent-filter for application/pdf
# - PdfViewerActivity (not exported)
# - FileProvider with ${applicationId}.fileprovider
# - AdMob meta-data
#

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa) storage
bin_dir = ./bin
