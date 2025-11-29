"""
Script de prueba para verificar la detección de ADB
"""
import os
import sys

print("Testing ADB detection logic...\n")

# Test 1: Verificar si bin/adb.exe existe
print("Test 1: Checking bin/adb.exe...")
if os.path.exists('bin/adb.exe'):
    print("  ✓ bin/adb.exe found")
    adb_command = 'bin/adb.exe'
else:
    print("  ✗ bin/adb.exe not found")
    
    # Test 2: Verificar si adb está en PATH
    print("\nTest 2: Checking system adb...")
    result = os.system('adb version >nul 2>&1')
    if result == 0:
        print("  ✓ System adb found")
        adb_command = 'adb'
    else:
        print("  ✗ System adb not found")
        adb_command = None

print(f"\nFinal decision: {adb_command if adb_command else 'No ADB available'}")

if adb_command:
    print(f"\nTesting command: {adb_command} version")
    os.system(f'{adb_command} version')
else:
    print("\n[ERROR] No ADB available!")
    print("Please install Android Platform Tools")
