import os
from dotenv import load_dotenv
import paramiko
from scp import SCPClient

load_dotenv()

# Configuration
local_root = os.getenv("LOCAL_ROOT")
remote_root = os.getenv("REMOTE_ROOT")
hostname = os.getenv("SCP_HOSTNAME")
port = os.getenv("SCP_PORT")
username = os.getenv("SCP_USERNAME")
password = os.getenv("SCP_PASSWORD")

# Create SSH client
ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, port=port, username=username, password=password)

# Create SCP client
scp = SCPClient(ssh.get_transport())

def remote_file_exists(remote_path, local_size):
    stdin, stdout, stderr = ssh.exec_command(f"stat -c %s \"{remote_path}\"")
    output = stdout.read().decode().strip()
    if output.isdigit() and int(output) == local_size:
        return True
    return False

# Recursively upload files
for root, dirs, files in os.walk(local_root):
    for file in files:
        local_path = os.path.join(root, file)
        relative_path = os.path.relpath(local_path, local_root)
        remote_path = os.path.join(remote_root, relative_path).replace("\\", "/")

        # Ensure remote directory exists
        ssh.exec_command(f"mkdir -p \"{os.path.dirname(remote_path)}\"")

        # Check if file exists with same size
        local_size = os.path.getsize(local_path)
        if remote_file_exists(remote_path, local_size):
            print(f"Skipping {relative_path} (already exists with same size)")
            continue

        print(f"Uploading {relative_path}")
        scp.put(local_path, remote_path)

scp.close()
ssh.close()
