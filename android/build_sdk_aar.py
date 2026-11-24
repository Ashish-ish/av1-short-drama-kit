import os
import shutil
import subprocess
import hashlib
import zipfile

REPO_ROOT = "/Users/ashish/Projects/av1decoder"
SDK_DIR = "/Users/ashish/Library/Android/sdk"
ANDROID_JAR = os.path.join(SDK_DIR, "platforms/android-37.0/android.jar")

SRC_DIR = os.path.join(REPO_ROOT, "android/av1-policy/src/main/java")
BUILD_DIR = os.path.join(REPO_ROOT, "build/aar")
DIST_DIR = os.path.join(REPO_ROOT, "dist/android")

os.makedirs(BUILD_DIR, exist_ok=True)
os.makedirs(DIST_DIR, exist_ok=True)

# 1. Resolve Classpath
GRADLE_CACHE = os.path.expanduser("~/.gradle/caches")
classpath_jars = [ANDROID_JAR]

def find_cached_jar(pattern):
    for root, dirs, files in os.walk(GRADLE_CACHE):
        for f in files:
            if pattern in f and f.endswith(".jar"):
                return os.path.join(root, f)
    return None

media3_common = find_cached_jar("media3-common-1.5.1-api.jar")
media3_exoplayer = find_cached_jar("media3-exoplayer-1.5.1-api.jar")
media3_datasource = find_cached_jar("media3-datasource-1.5.1-api.jar")
media3_database = find_cached_jar("media3-database-1.5.1-api.jar")
annotation_jar = find_cached_jar("annotation-jvm-1.8.1.jar")

for j in [media3_common, media3_exoplayer, media3_datasource, media3_database, annotation_jar]:
    if j and os.path.exists(j):
        classpath_jars.append(j)

classpath_str = ":".join(classpath_jars)

# 2. Collect Java Sources
java_sources = []
for root, dirs, files in os.walk(SRC_DIR):
    for f in files:
        if f.endswith(".java"):
            java_sources.append(os.path.join(root, f))

print(f"Compiling {len(java_sources)} Java source files for Android AAR...")
classes_dir = os.path.join(BUILD_DIR, "classes")
if os.path.exists(classes_dir):
    shutil.rmtree(classes_dir)
os.makedirs(classes_dir, exist_ok=True)

cmd_javac = [
    "javac",
    "-source", "17",
    "-target", "17",
    "-cp", classpath_str,
    "-d", classes_dir
] + java_sources

subprocess.run(cmd_javac, check=True)
print("SUCCESS: Bytecode compiled.")

# 3. Build classes.jar
classes_jar = os.path.join(BUILD_DIR, "classes.jar")
cmd_jar = ["jar", "cf", classes_jar, "-C", classes_dir, "."]
subprocess.run(cmd_jar, check=True)

# 4. Build sources.jar
sources_jar = os.path.join(DIST_DIR, "av1-policy-0.1.0-sources.jar")
cmd_src_jar = ["jar", "cf", sources_jar, "-C", SRC_DIR, "."]
subprocess.run(cmd_src_jar, check=True)

# 5. Manifest & Proguard
manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.verticaldrama.av1policy">
    <uses-sdk android:minSdkVersion="26" android:targetSdkVersion="34" />
</manifest>
"""
manifest_file = os.path.join(BUILD_DIR, "AndroidManifest.xml")
with open(manifest_file, "w") as f:
    f.write(manifest_content)

rtxt_file = os.path.join(BUILD_DIR, "R.txt")
with open(rtxt_file, "w") as f:
    f.write("")

consumer_rules = os.path.join(BUILD_DIR, "consumer-rules.pro")
with open(consumer_rules, "w") as f:
    f.write("-keep class com.verticaldrama.av1policy.** { *; }\n")

# 6. Package AAR
aar_path = os.path.join(DIST_DIR, "av1-policy-0.1.0.aar")
if os.path.exists(aar_path):
    os.remove(aar_path)

with zipfile.ZipFile(aar_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(manifest_file, "AndroidManifest.xml")
    z.write(classes_jar, "classes.jar")
    z.write(rtxt_file, "R.txt")
    z.write(consumer_rules, "consumer-rules.pro")

print(f"SUCCESS: Created Android AAR at {aar_path}")

# 7. Generate Maven POM
pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.verticaldrama</groupId>
    <artifactId>av1-policy</artifactId>
    <version>0.1.0</version>
    <packaging>aar</packaging>
    <name>AV1 Policy Android SDK</name>
    <description>Hardware and platform dav1d playback policy coordinator and drama-tuned preload controller</description>
    <url>https://github.com/Ashish-ish/av1-short-drama-kit</url>
    <licenses>
        <license>
            <name>Apache License, Version 2.0</name>
            <url>http://www.apache.org/licenses/LICENSE-2.0.txt</url>
        </license>
    </licenses>
    <dependencies>
        <dependency>
            <groupId>androidx.media3</groupId>
            <artifactId>media3-exoplayer</artifactId>
            <version>1.3.1</version>
            <scope>compile</scope>
        </dependency>
        <dependency>
            <groupId>androidx.media3</groupId>
            <artifactId>media3-common</artifactId>
            <version>1.3.1</version>
            <scope>compile</scope>
        </dependency>
        <dependency>
            <groupId>androidx.media3</groupId>
            <artifactId>media3-datasource</artifactId>
            <version>1.3.1</version>
            <scope>compile</scope>
        </dependency>
    </dependencies>
</project>
"""
pom_path = os.path.join(DIST_DIR, "av1-policy-0.1.0.pom")
with open(pom_path, "w") as f:
    f.write(pom_content)

# 8. Checksum
with open(aar_path, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

with open(os.path.join(DIST_DIR, "av1-policy-0.1.0.aar.sha256"), "w") as f:
    f.write(f"{sha}  av1-policy-0.1.0.aar\n")

print(f"Android AAR SHA-256: {sha}")
