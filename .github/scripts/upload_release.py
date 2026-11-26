import os
import sys
import json
import hashlib
import subprocess
import urllib.request
import urllib.error

# Force utf-8 for Windows console
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

app = os.environ["APP"]
version = os.environ["VERSION"]
arch = os.environ["ARCH"]
tag = os.environ.get("TAG_INPUT") or f"v{version}"
token = os.environ["FORGE_TOKEN"]

base_url = "https://code.yumedevs.com/api/v1"
repo_path = f"Alejandro/{app}"
dist_dir = os.path.join(os.environ["APP_DIR"], "dist", "release")

print(f"[*] Processing Windows release for {repo_path} at tag {tag}")

# 1. Fetch release info
req = urllib.request.Request(
    f"{base_url}/repos/{repo_path}/releases/tags/{tag}",
    headers={"Authorization": f"token {token}", "User-Agent": "Yume-Windows-Builder"}
)
try:
    with urllib.request.urlopen(req) as resp:
        release_info = json.loads(resp.read().decode("utf-8"))
except urllib.error.HTTPError as e:
    print(f"Error: Release {tag} not found on {repo_path} ({e})")
    sys.exit(1)

release_id = release_info["id"]
existing_assets = {a["name"]: a for a in release_info.get("assets", [])}
print(f"[*] Found release ID {release_id} with {len(existing_assets)} existing assets")

# 2. Collect files to upload from dist/release (.msi, .exe, .zip)
files_to_hash = {}
if os.path.isdir(dist_dir):
    for f in os.listdir(dist_dir):
        if f.endswith(".msi") or f.endswith(".zip") or f.endswith(".exe"):
            if f != "SHA256SUMS.txt":
                files_to_hash[f] = os.path.join(dist_dir, f)

if not files_to_hash:
    print("Error: No .msi or .zip artifacts found to upload!")
    sys.exit(1)

new_hashes = {}
for fname, fpath in files_to_hash.items():
    h = hashlib.sha256()
    with open(fpath, "rb") as bf:
        while chunk := bf.read(65536):
            h.update(chunk)
    digest = h.hexdigest().upper()
    new_hashes[fname] = digest
    print(f"[+] Computed SHA-256 for {fname}: {digest}")

# 3. Read and merge existing SHA256SUMS.txt
all_sums = {}
if "SHA256SUMS.txt" in existing_assets:
    # Use Authorization header for download
    sums_url = existing_assets["SHA256SUMS.txt"]["browser_download_url"]
    try:
        sums_req = urllib.request.Request(
            sums_url,
            headers={"Authorization": f"token {token}", "User-Agent": "Yume-Windows-Builder"}
        )
        with urllib.request.urlopen(sums_req) as resp:
            content = resp.read().decode("utf-8-sig", errors="replace")
            for line in content.splitlines():
                parts = line.strip().split(None, 1)
                if len(parts) == 2 and len(parts[0]) == 64:
                    clean_name = parts[1].lstrip("*")
                    all_sums[clean_name] = parts[0].upper()
            print(f"[*] Loaded {len(all_sums)} existing checksums from release")
    except Exception as e:
        print(f"[!] Warning reading existing SHA256SUMS.txt: {e}")

# Merge new hashes
for fname, digest in new_hashes.items():
    all_sums[fname] = digest

# Write merged SHA256SUMS.txt (pure ASCII, LF only)
sums_file_path = os.path.join(dist_dir, "SHA256SUMS.txt")
with open(sums_file_path, "wb") as sf:
    for fname in sorted(all_sums.keys()):
        line = f"{all_sums[fname]}  {fname}\n"
        sf.write(line.encode("ascii"))
print(f"[*] Generated clean SHA256SUMS.txt with {len(all_sums)} total entries")

# 4. Upload helper using curl
def upload_file(filename, filepath):
    if filename in existing_assets:
        asset_id = existing_assets[filename]["id"]
        print(f"[-] Deleting previous asset '{filename}' (ID: {asset_id})...")
        del_cmd = [
            "curl", "-s", "-X", "DELETE",
            "-H", f"Authorization: token {token}",
            f"{base_url}/repos/{repo_path}/releases/{release_id}/assets/{asset_id}"
        ]
        subprocess.run(del_cmd, check=True)

    print(f"[+] Uploading '{filename}'...")
    up_cmd = [
        "curl", "-s", "--fail-with-body", "-X", "POST",
        "-H", f"Authorization: token {token}",
        "-F", f"attachment=@{filepath}",
        f"{base_url}/repos/{repo_path}/releases/{release_id}/assets?name={filename}"
    ]
    res = subprocess.run(up_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error uploading {filename} (exit {res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        sys.exit(1)
    print(f"[OK] Successfully uploaded '{filename}'")

# Upload MSIs and ZIPs
for fname, fpath in files_to_hash.items():
    upload_file(fname, fpath)

# Upload updated SHA256SUMS.txt
upload_file("SHA256SUMS.txt", sums_file_path)
print("[OK] All Windows release assets uploaded successfully to Gitea!")
