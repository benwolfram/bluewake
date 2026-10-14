#!/usr/bin/env python3
"""Build generated SAF adapter instrumentation. --serial runs on an already
booted, explicitly selected emulator; this script never creates/boots an AVD.
Only the standalone dev.bluewake.hdinputs.test package is installed/removed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/wwhd_android_inputs"
PACKAGE = "dev.bluewake.hdinputs.test"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk")))
    parser.add_argument("--jdk", type=Path)
    parser.add_argument("--serial", help="Explicit emulator serial; omitted means build only")
    args = parser.parse_args()
    out = ROOT / "build/wwhd-disc-import/android-inputs"
    out.mkdir(parents=True, exist_ok=True)
    commands = []
    env = dict(os.environ)
    jdk = args.jdk or Path(subprocess.check_output(["/usr/libexec/java_home"], text=True).strip())
    env["JAVA_HOME"] = str(jdk)
    tools = args.sdk / "build-tools/36.0.0"
    jar = args.sdk / "platforms/android-36/android.jar"
    ndk = args.sdk / "ndk/29.0.14206865/toolchains/llvm/prebuilt/darwin-x86_64/bin/aarch64-linux-android28-clang++"

    def run(command, *, check=True, timeout=120):
        command = list(map(str, command))
        commands.append(shlex.join(command))
        result = subprocess.run(command, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout)
        with (out / "build.log").open("a") as log:
            log.write(shlex.join(command) + "\n" + result.stdout)
        if check and result.returncode:
            raise RuntimeError(result.stdout)
        return result.stdout

    (out / "build.log").write_text("")
    classes = out / "classes"
    classes.mkdir(exist_ok=True)
    sources = [ROOT / "android/java/dev/bluewake/android/HDImportInputs.java", FIXTURES / "HDImportInputsTest.java"]
    run([jdk / "bin/javac", "--release", "11", "-Xlint:all", "-classpath", jar, "-d", classes, *sources])
    run([jdk / "bin/jar", "--create", "--file", out / "classes.jar", "-C", classes, "."])
    run([tools / "d8", "--release", "--min-api", "28", "--lib", jar, "--output", out, out / "classes.jar"])
    library = out / "libwwhd_inputs_probe.so"
    run([ndk, "-std=c++17", "-shared", "-fPIC", "-static-libstdc++", "-O1", "-Wall", "-Wextra",
         "-I", ROOT / "runtime/host/src", FIXTURES / "native_probe.cpp",
         ROOT / "runtime/host/src/wwhd/disc_image.cpp", "-o", library])
    unsigned = out / "unsigned.apk"
    run([tools / "aapt2", "link", "-o", unsigned, "--manifest", FIXTURES / "AndroidManifest.xml", "-I", jar])
    with zipfile.ZipFile(unsigned, "a") as archive:
        archive.write(out / "classes.dex", "classes.dex")
        archive.write(library, "lib/arm64-v8a/libwwhd_inputs_probe.so")
    run([tools / "zipalign", "-f", "4", unsigned, out / "aligned.apk"])
    key = out / "generated-test.keystore"
    if not key.exists():
        run([jdk / "bin/keytool", "-genkeypair", "-keystore", key, "-storepass", "synthetic-only",
             "-keypass", "synthetic-only", "-alias", "test", "-keyalg", "RSA", "-validity", "30",
             "-dname", "CN=Generated adapter tests", "-noprompt"])
    apk = out / "wwhd-inputs-test.apk"
    run([tools / "apksigner", "sign", "--ks", key, "--ks-pass", "pass:synthetic-only", "--out", apk, out / "aligned.apk"])
    run([tools / "apksigner", "verify", apk])
    if args.serial:
        if not args.serial.startswith("emulator-"):
            raise ValueError("This generated fixture runner only accepts an emulator serial")
        adb = [args.sdk / "platform-tools/adb", "-s", args.serial]
        if run([*adb, "shell", "getprop", "ro.kernel.qemu"]).strip() != "1":
            raise ValueError("Selected device is not an emulator")
        run([*adb, "install", "-r", "-t", apk])
        try:
            result = run([*adb, "shell", "am", "instrument", "-w", "-r",
                          PACKAGE + "/dev.bluewake.android.HDImportInputsTest"])
            (out / "instrumentation.log").write_text(result)
            if "INSTRUMENTATION_CODE: -1" not in result or "generated Android document-adapter cases" not in result or "FAIL:" in result:
                raise RuntimeError(result)
            print(result)
        finally:
            run([*adb, "uninstall", PACKAGE])
    (out / "commands.sh").write_text("#!/bin/sh\nset -eu\ncd " + shlex.quote(str(ROOT)) + "\n" + "\n".join(commands) + "\n")
    files = [*sources, FIXTURES / "native_probe.cpp", FIXTURES / "AndroidManifest.xml", Path(__file__),
             ROOT / "runtime/host/src/wwhd/disc_image.cpp", ROOT / "runtime/host/src/wwhd/disc_image.h"]
    (out / "proof.json").write_text(json.dumps({"serial": args.serial, "apk": str(apk),
        "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}, indent=2) + "\n")
    print("Evidence: " + str(out))


if __name__ == "__main__":
    main()
