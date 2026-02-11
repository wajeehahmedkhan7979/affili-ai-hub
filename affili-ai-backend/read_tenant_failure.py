
try:
    with open('tenant_isolation_failure.txt', 'r', encoding='utf-16') as f:
        content = f.read()
except:
    with open('tenant_isolation_failure.txt', 'r', encoding='utf-8') as f:
        content = f.read()

lines = content.splitlines()
failed_lines = [l for l in lines if 'FAILED' in l or 'ERROR' in l]
print("--- SUMMARY ---")
print('\n'.join(failed_lines[:20]))

print("\n--- CONTEXT ---")
try:
    start_idx = [i for i,l in enumerate(lines) if 'FAILED' in l][0]
    print('\n'.join(lines[start_idx:start_idx+50]))
except IndexError:
    print("No FAILED lines found")
