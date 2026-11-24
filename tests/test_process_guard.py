from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest


@unittest.skipUnless(os.name == "nt", "Windows process lifecycle check")
class ProcessGuardTests(unittest.TestCase):
    def test_killing_app_process_also_ends_its_native_child(self):
        script = """
from dm_migration.process_guard import ProcessGuard
import subprocess, sys, time
guard = ProcessGuard()
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])
guard.attach(child)
print(child.pid, flush=True)
time.sleep(20)
"""
        parent = subprocess.Popen([sys.executable, "-u", "-c", script],
            cwd=Path(__file__).resolve().parents[1], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        child_handle = None
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        try:
            line = parent.stdout.readline()
            if not line:
                self.fail(parent.stderr.read().decode(errors="replace"))
            child_handle = kernel.OpenProcess(0x1001, False, int(line.strip()))
            self.assertTrue(child_handle)
            parent.terminate()
            parent.wait(timeout=5)
            code = wintypes.DWORD(259)
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                kernel.GetExitCodeProcess(child_handle, ctypes.byref(code))
                if code.value != 259:
                    break
                time.sleep(0.02)
            self.assertNotEqual(code.value, 259, "Native child survived the app process")
        finally:
            if parent.poll() is None:
                parent.terminate()
                parent.wait(timeout=5)
            if child_handle:
                kernel.TerminateProcess(child_handle, 1)
                kernel.CloseHandle(child_handle)
            if parent.stdout:
                parent.stdout.close()
            if parent.stderr:
                parent.stderr.close()
