from pathlib import Path

f = Path(r"C:\projects\Data_Engineering\textgen\output\generated_textbooks\Physics\Unit01_Unit_1__Units_and_Measurement.md")
lines = f.read_text(encoding="utf-8").split('\n')

print(f"Total lines: {len(lines)}\n")
print("First 80 lines:")
print("─" * 60)
for i, line in enumerate(lines[:80], 1):
    print(f"{i:3}: {repr(line)}")