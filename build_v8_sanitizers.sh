#!/bin/bash
set -e

# Instructions:
# 1. This script automates the process of fetching and building V8 with various sanitizers.
# 2. It requires `git`, `python3`, `curl` and `sudo` (for dependency installation).
# 3. Run this script in a directory where you want to store the `v8` source code.

echo "Starting V8 build setup..."

# Setup depot_tools
if [ ! -d "depot_tools" ]; then
    echo "Cloning depot_tools..."
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
fi
export PATH=$PWD/depot_tools:$PATH

# Fetch V8
if [ ! -d "v8" ]; then
    echo "Fetching v8 (this may take a while)..."
    fetch v8
else
    echo "V8 directory exists. Syncing..."
    cd v8
    gclient sync
    cd ..
fi

cd v8

# Install build dependencies
echo "Installing build dependencies... (requires sudo)"
# Using --no-prompt to avoid interactive questions, but sudo might still ask for password.
./build/install-build-deps.sh --no-prompt

# Helper function to build
build_variant() {
    local dir=$1
    local args=$2
    echo "------------------------------------------------"
    echo "Building $dir configuration..."
    echo "Args: $args"
    echo "------------------------------------------------"

    gn gen "out/$dir" --args="$args"
    ninja -C "out/$dir" d8

    if [ -f "out/$dir/d8" ]; then
        echo "Build $dir successful. Binary at out/$dir/d8"
    else
        echo "Build $dir failed to produce d8 binary."
    fi
}

# ASan (AddressSanitizer)
# Checks for memory errors like out-of-bounds accesses, use-after-free, etc.
build_variant "asan" 'is_asan=true is_debug=false is_component_build=false v8_enable_test_features=true'

# UBSan (UndefinedBehaviorSanitizer)
# Checks for undefined behavior like integer overflow, null pointer dereference, etc.
build_variant "ubsan" 'is_ubsan=true is_debug=false is_component_build=false v8_enable_test_features=true'

# MSan (MemorySanitizer)
# Checks for use of uninitialized memory.
# Note: MSan requires instrumented system libraries. We use use_locally_built_instrumented_libraries=false
# to attempt to build without them, which might catch fewer issues or require specific env setup,
# but allows building on standard systems.
build_variant "msan" 'is_msan=true is_debug=false is_component_build=false v8_enable_test_features=true msan_track_origins=2 use_locally_built_instrumented_libraries=false'

# TSan (ThreadSanitizer)
# Checks for data races.
build_variant "tsan" 'is_tsan=true is_debug=false is_component_build=false v8_enable_test_features=true'

echo "All requested builds have been attempted."
