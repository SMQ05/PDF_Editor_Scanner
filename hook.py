"""
Buildozer p4a hook for PDF Scanner app.

This hook runs before python-for-android build steps to:
1. Copy our custom AndroidManifest.tmpl.xml into the p4a templates
2. Patch build.gradle for PDFBox META-INF conflict handling

Usage: Set in buildozer.spec:
    p4a.hook = hook.py
"""
import os
import shutil
import glob
from os.path import join, exists, dirname, abspath


# Use __file__ for reliable source directory detection
SOURCE_DIR = dirname(abspath(__file__))


def get_template_dir(build_dir):
    """Find the AndroidManifest template directory in p4a."""
    candidates = [
        join(build_dir, 'android', 'platform', 'python-for-android',
             'pythonforandroid', 'bootstraps', 'sdl2', 'build', 'templates'),
    ]
    
    for path in candidates:
        if exists(path):
            return path
    
    # Try glob patterns for varying build structures
    patterns = [
        join(build_dir, 'android', 'platform', 'build-*', 'dists', '*', 'templates'),
    ]
    
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    
    return None


def get_gradle_files(build_dir):
    """Find all build.gradle files in the build output."""
    patterns = [
        join(build_dir, 'android', 'platform', 'build-*', 'dists', '*', 'build.gradle'),
        join(build_dir, 'android', 'platform', 'python-for-android', 
             'pythonforandroid', 'bootstraps', 'sdl2', 'build', 'build.gradle'),
    ]
    
    results = []
    for pattern in patterns:
        results.extend(glob.glob(pattern))
    
    return results


def copy_manifest_template(build_dir):
    """Copy our custom manifest template to p4a templates."""
    source = join(SOURCE_DIR, 'android', 'AndroidManifest.tmpl.xml')
    
    if not exists(source):
        print(f"[hook.py] WARNING: Manifest template not found: {source}")
        return False
    
    template_dir = get_template_dir(build_dir)
    if not template_dir:
        print("[hook.py] INFO: p4a template directory not found yet (normal on first run)")
        return False
    
    dest = join(template_dir, 'AndroidManifest.tmpl.xml')
    
    print(f"[hook.py] Copying manifest template:")
    print(f"  Source: {source}")
    print(f"  Dest:   {dest}")
    
    shutil.copy2(source, dest)
    return True


PACKAGING_OPTIONS = '''    packagingOptions {
        exclude 'META-INF/DEPENDENCIES'
        exclude 'META-INF/LICENSE'
        exclude 'META-INF/LICENSE.txt'
        exclude 'META-INF/license.txt'
        exclude 'META-INF/NOTICE'
        exclude 'META-INF/NOTICE.txt'
        exclude 'META-INF/notice.txt'
        exclude 'META-INF/ASL2.0'
        exclude 'META-INF/*.kotlin_module'
    }
'''


def patch_gradle_for_pdfbox(build_dir):
    """Add META-INF exclusions to build.gradle for PDFBox compatibility.
    
    Uses line-based insertion after 'android {' for robustness.
    Idempotent: skips if our excludes already present.
    """
    gradle_files = get_gradle_files(build_dir)
    
    if not gradle_files:
        print("[hook.py] INFO: build.gradle not found yet (normal before first build)")
        return False
    
    patched_any = False
    
    for gradle_file in gradle_files:
        if not exists(gradle_file):
            continue
            
        with open(gradle_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        content = ''.join(lines)
        
        # Check if already patched (idempotent)
        if "META-INF/DEPENDENCIES" in content:
            print(f"[hook.py] {gradle_file} already patched, skipping")
            continue
        
        # Find 'android {' line and insert packagingOptions after it
        new_lines = []
        inserted = False
        
        for line in lines:
            new_lines.append(line)
            
            # Insert after 'android {' line
            if not inserted and line.strip().startswith('android') and '{' in line:
                new_lines.append(PACKAGING_OPTIONS)
                inserted = True
        
        if inserted:
            with open(gradle_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"[hook.py] Patched {gradle_file} with packagingOptions")
            patched_any = True
        else:
            print(f"[hook.py] WARNING: Could not find 'android {{' in {gradle_file}")
    
    return patched_any


# ============================================================
# Hook entry points called by python-for-android / Buildozer
# ============================================================

def prebuild_android(build_dir):
    """Called before Android build starts (p4a hook)."""
    print("[hook.py] prebuild_android called")
    
    # Copy manifest template
    copy_manifest_template(build_dir)
    
    # Patch Gradle BEFORE compilation (critical for PDFBox)
    patch_gradle_for_pdfbox(build_dir)


def after_apk(build_dir):
    """Called after APK is created (p4a hook)."""
    print("[hook.py] after_apk called - build complete")


# Alternative hook names used by some p4a versions
pre_build = prebuild_android
post_build = after_apk


# Buildozer direct hook support
def before_build():
    """Buildozer pre-build hook."""
    print("[hook.py] before_build called")
    
    build_dir = os.environ.get('BUILDOZER_BUILD_DIR', join(SOURCE_DIR, '.buildozer'))
    
    # Copy manifest template
    copy_manifest_template(build_dir)
    
    # Patch Gradle BEFORE compilation
    patch_gradle_for_pdfbox(build_dir)


def after_build():
    """Buildozer post-build hook."""
    print("[hook.py] after_build called")
