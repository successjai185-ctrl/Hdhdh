import subprocess
import os
import sys

def verify_overflow():
    translator_path = "./angle_src/out/Sanitizers/angle_shader_translator"
    shader_path = "overflow_test.vert"

    if not os.path.exists(translator_path):
        print("Error: Translator binary not found.")
        return

    print("Running overflow verification...")
    # Using ESSL 3.00 because array of arrays is an ES 3.1 feature?
    # Or at least 3.00. 65536 is large, might hit other limits.
    # Let's try -s=w (WebGL 1.0) first, checking if it rejects it.
    # Actually array of arrays is ES 3.1. -s=e31

    # We'll try multiple specs.
    specs = ["-s=e31", "-s=e32", "-s=w2"]

    for spec in specs:
        print(f"Testing with {spec}...")
        try:
            result = subprocess.run(
                [translator_path, spec, "-b=e", shader_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stderr + result.stdout
            print(f"Return code: {result.returncode}")
            # print(output)

            if "AddressSanitizer" in output or "UndefinedBehaviorSanitizer" in output or result.returncode < 0:
                print("CRASH/SANITIZER ERROR DETECTED!")
                print(output)
                return True

            if "Size of declared variable exceeds implementation-defined limit" in output:
                print("Validator caught the size (Correct behavior).")
            else:
                print("Validator did NOT complain about size (Potential Bypass).")
                if result.returncode == 0:
                     print("Compilation SUCCESSFUL despite massive size (Bypass Confirmed).")

        except subprocess.TimeoutExpired:
            print("Timeout expired.")

    return False

if __name__ == "__main__":
    verify_overflow()
