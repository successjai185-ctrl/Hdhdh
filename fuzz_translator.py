import subprocess
import random
import os
import sys
import time

# Valid basic shader to mutate
BASE_SHADER = """
precision mediump float;
attribute vec4 a_position;
varying vec4 v_color;
void main() {
    v_color = vec4(1.0, 0.5, 0.2, 1.0);
    gl_Position = a_position;
}
"""

def mutate(content):
    """Apply random mutations to the content."""
    data = list(content.encode('utf-8'))
    num_mutations = random.randint(1, 5)

    for _ in range(num_mutations):
        mutation_type = random.choice(['flip', 'delete', 'insert', 'shuffle'])

        if len(data) == 0:
            data = list(b"void main(){}")
            continue

        idx = random.randint(0, len(data) - 1)

        if mutation_type == 'flip':
            data[idx] ^= random.randint(0, 255)
        elif mutation_type == 'delete':
            del data[idx]
        elif mutation_type == 'insert':
            data.insert(idx, random.randint(0, 255))
        elif mutation_type == 'shuffle':
            end = random.randint(idx, len(data))
            sub = data[idx:end]
            random.shuffle(sub)
            data[idx:end] = sub

    try:
        return bytes(data).decode('utf-8', errors='ignore')
    except:
        return BASE_SHADER # Fallback

def run_fuzzer(iterations=100):
    translator_path = "./angle_src/out/Sanitizers/angle_shader_translator"
    if not os.path.exists(translator_path):
        print(f"Error: Translator not found at {translator_path}")
        return

    print(f"Starting fuzzer for {iterations} iterations...")

    crashes = 0
    start_time = time.time()

    for i in range(iterations):
        if i % 10 == 0:
            print(f"Iteration {i}...")

        # 50% chance of fresh mutation from base, 50% random garbage
        if random.random() < 0.8:
            test_content = mutate(BASE_SHADER)
        else:
            test_content = mutate("void main() { " + "A" * random.randint(0, 100) + " }")

        with open("fuzz_input.vert", "w") as f:
            f.write(test_content)

        try:
            # -s=w (WebGL) -b=e (ESSL) are standard
            result = subprocess.run(
                [translator_path, "-s=w", "-b=e", "fuzz_input.vert"],
                capture_output=True,
                text=True,
                timeout=2
            )

            output = result.stderr + result.stdout

            # Check for Sanitizer errors
            if "AddressSanitizer" in output or "UndefinedBehaviorSanitizer" in output or result.returncode < 0 or result.returncode == 139: # 139 is SIGSEGV
                print(f"CRASH FOUND at iteration {i}!")
                crashes += 1
                crash_filename = f"crash_{int(time.time())}_{i}.vert"
                with open(crash_filename, "w") as cf:
                    cf.write(test_content)
                with open(crash_filename + ".log", "w") as lf:
                    lf.write(output)
                print(f"Saved crash to {crash_filename}")
                # We can stop after finding one, or verify.
                # For this task, let's stop to analyze.
                return

        except subprocess.TimeoutExpired:
            print("Timeout expired.")
            continue
        except Exception as e:
            print(f"Execution error: {e}")

    print(f"Fuzzing complete. {crashes} crashes found.")

if __name__ == "__main__":
    run_fuzzer(500)
