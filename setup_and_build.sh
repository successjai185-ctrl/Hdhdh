#!/bin/bash
set -e

# Setup Depot Tools
if [ ! -d "depot_tools" ]; then
    echo "Cloning depot_tools..."
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
fi
export PATH="$PWD/depot_tools:$PATH"

# Setup ANGLE
if [ ! -d "angle_src" ]; then
    echo "Cloning ANGLE..."
    mkdir angle_src
    cd angle_src
    # Create .gclient file manually to avoid fetch issues
    echo 'solutions = [
      {
        "name": ".",
        "url": "https://chromium.googlesource.com/angle/angle.git",
        "deps_file": "DEPS",
        "managed": False,
        "custom_vars": {},
      },
    ]
    ' > .gclient
    cd ..
fi

cd angle_src

# Sync dependencies
echo "Syncing dependencies (this may take a while)..."
gclient sync --no-history

# Configure Build with Sanitizers
echo "Configuring build with ASan and UBSan..."
gn gen out/Sanitizers --args='is_asan=true is_ubsan=true is_debug=false'

# Build
echo "Building full ANGLE library (libEGL, libGLESv2) and shader translator..."
autoninja -C out/Sanitizers angle_shader_translator libEGL libGLESv2

echo "Build complete. Output in angle_src/out/Sanitizers/"
echo "Verifying sanitizers..."
if readelf -s out/Sanitizers/libGLESv2.so | grep -q "__asan_init"; then
    echo "ASan detected."
else
    echo "ASan NOT detected."
fi

if readelf -s out/Sanitizers/angle_shader_translator | grep -q "__ubsan_handle"; then
    echo "UBSan detected."
else
    echo "UBSan NOT detected."
fi
