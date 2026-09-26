"""Windows Credential Manager storage. Secrets never enter V3MM config or logs."""
import ctypes
import os
from ctypes import wintypes

TARGET = "Victoria3ModManager/GeminiAPI"
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2


class CREDENTIALW(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)), ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD), ("Attributes", wintypes.LPVOID),
                ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]


class CredentialStore:
    def __init__(self, target: str = TARGET): self.target = target
    def _api(self):
        if os.name != "nt": raise OSError("Windows Credential Manager is only available on Windows.")
        return ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    def set(self, secret: str) -> None:
        if not secret.strip(): raise ValueError("API key is empty.")
        api = self._api(); blob = secret.encode("utf-16-le"); buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = CREDENTIALW(Type=CRED_TYPE_GENERIC, TargetName=self.target, CredentialBlobSize=len(blob),
                                 CredentialBlob=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)), Persist=CRED_PERSIST_LOCAL_MACHINE,
                                 UserName="V3MM")
        api.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]; api.CredWriteW.restype = wintypes.BOOL
        if not api.CredWriteW(ctypes.byref(credential), 0): raise ctypes.WinError(ctypes.get_last_error())
    def get(self) -> str | None:
        api = self._api(); pointer = ctypes.POINTER(CREDENTIALW)()
        api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]; api.CredReadW.restype = wintypes.BOOL
        api.CredFree.argtypes = [wintypes.LPVOID]
        if not api.CredReadW(self.target, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168: return None
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            raw = ctypes.string_at(pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize)
            return raw.decode("utf-16-le")
        finally: api.CredFree(pointer)
    def delete(self) -> None:
        api = self._api(); api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]; api.CredDeleteW.restype = wintypes.BOOL
        if not api.CredDeleteW(self.target, CRED_TYPE_GENERIC, 0) and ctypes.get_last_error() != 1168: raise ctypes.WinError(ctypes.get_last_error())
    def exists(self) -> bool:
        try: return bool(self.get())
        except OSError: return False
