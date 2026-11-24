import os
import shutil
import subprocess
import hashlib

XCODE_DEV = "/Applications/Xcode.app/Contents/Developer"
SWIFTC = f"{XCODE_DEV}/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc"
XCODEBUILD = f"{XCODE_DEV}/usr/bin/xcodebuild"

DEVICE_SDK = f"{XCODE_DEV}/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS27.2.sdk"
SIM_SDK = f"{XCODE_DEV}/Platforms/iPhoneSimulator.platform/Developer/SDKs/iPhoneSimulator27.2.sdk"

REPO_ROOT = "/Users/ashish/Projects/av1decoder"
SOURCES_DIR = os.path.join(REPO_ROOT, "ios/AV1Policy/Sources/AV1Policy")
BUILD_DIR = os.path.join(REPO_ROOT, "build/xcframework")
DIST_DIR = os.path.join(REPO_ROOT, "dist/ios")

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(DIST_DIR, exist_ok=True)

swift_sources = [
    os.path.join(SOURCES_DIR, f)
    for f in sorted(os.listdir(SOURCES_DIR))
    if f.endswith(".swift")
]

def make_framework_plist(name, min_os="14.0"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>{name}</string>
    <key>CFBundleIdentifier</key>
    <string>com.verticaldrama.{name.lower()}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{name}</string>
    <key>CFBundlePackageType</key>
    <string>FMWK</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>MinimumOSVersion</key>
    <string>{min_os}</string>
</dict>
</plist>
"""

def build_slice(platform_name, sdk_path, target_triple, out_dir):
    fmwk_dir = os.path.join(out_dir, "AV1Policy.framework")
    if os.path.exists(fmwk_dir):
        shutil.rmtree(fmwk_dir)
    os.makedirs(fmwk_dir, exist_ok=True)

    modules_dir = os.path.join(fmwk_dir, "Modules/AV1Policy.swiftmodule")
    headers_dir = os.path.join(fmwk_dir, "Headers")
    os.makedirs(modules_dir, exist_ok=True)
    os.makedirs(headers_dir, exist_ok=True)

    # Info.plist
    with open(os.path.join(fmwk_dir, "Info.plist"), "w") as f:
        f.write(make_framework_plist("AV1Policy"))

    # Compile framework binary
    bin_path = os.path.join(fmwk_dir, "AV1Policy")
    objc_header = os.path.join(headers_dir, "AV1Policy-Swift.h")

    arch = target_triple.split("-")[0]
    module_base = os.path.join(modules_dir, f"{target_triple}")

    cmd = [
        SWIFTC,
        "-target", target_triple,
        "-sdk", sdk_path,
        "-module-name", "AV1Policy",
        "-swift-version", "5",
        "-emit-library",
        "-emit-module",
        "-emit-module-path", f"{module_base}.swiftmodule",
        "-emit-module-interface-path", f"{module_base}.swiftinterface",
        "-enable-library-evolution",
        "-emit-objc-header",
        "-emit-objc-header-path", objc_header,
        "-parse-as-library",
        "-O",
        "-framework", "Foundation",
        "-framework", "AVFoundation",
        "-framework", "VideoToolbox",
        "-framework", "CoreMedia",
        "-o", bin_path
    ] + swift_sources

    print(f"Building slice for {platform_name} ({target_triple})...")
    subprocess.run(cmd, check=True)
    return fmwk_dir

# 1. Build Device slice (arm64)
device_fmwk = build_slice("iOS Device", DEVICE_SDK, "arm64-apple-ios14.0", os.path.join(BUILD_DIR, "device"))

# 2. Build Simulator slice (arm64)
sim_fmwk = build_slice("iOS Simulator", SIM_SDK, "arm64-apple-ios14.0-simulator", os.path.join(BUILD_DIR, "simulator"))

# 3. Create XCFramework
out_xcframework = os.path.join(DIST_DIR, "AV1Policy.xcframework")
if os.path.exists(out_xcframework):
    shutil.rmtree(out_xcframework)

cmd_xcfmwk = [
    XCODEBUILD,
    "-create-xcframework",
    "-framework", device_fmwk,
    "-framework", sim_fmwk,
    "-output", out_xcframework
]

print("Packaging XCFramework...")
subprocess.run(cmd_xcfmwk, check=True)
print(f"SUCCESS: Created XCFramework at {out_xcframework}")

# 4. Zip archive for Carthage / SPM binaryTarget distribution
zip_path = os.path.join(DIST_DIR, "AV1Policy.xcframework.zip")
if os.path.exists(zip_path):
    os.remove(zip_path)

subprocess.run(["zip", "-r", "-y", zip_path, "AV1Policy.xcframework"], cwd=DIST_DIR, check=True)

# 5. Compute SHA256 checksum
with open(zip_path, "rb") as f:
    sha256 = hashlib.sha256(f.read()).hexdigest()

checksum_path = os.path.join(DIST_DIR, "AV1Policy.xcframework.zip.sha256")
with open(checksum_path, "w") as f:
    f.write(f"{sha256}  AV1Policy.xcframework.zip\\n")

print(f"SUCCESS: Created {zip_path}")
print(f"SHA-256 Checksum: {sha256}")
