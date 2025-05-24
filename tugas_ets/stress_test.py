import subprocess
import csv
import os
from itertools import product
import time
import signal

server = "server_pool.py"
client = "client_pool.py"

operations = ["download", "upload"]
filesizes = [10, 50, 100]
client_workers = [1, 5, 50]
server_workers = [1, 5, 50]
server_modes = ["thread", "process"]
client_modes = ["thread"]

ip = "172.16.16.101"
port = 10000

no = 1

output_csv = "ss_stress_test_results.csv"

if os.path.exists(output_csv):
    os.remove(output_csv)

headers = [
    "No",
    "Operation", "Volume (MB)",
    "Client Mode", "Client Workers",
    "Server Mode", "Server Workers",
    "Total Time", "Throughput (Bps)", "Successes", "Fails"
]

with open(output_csv, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)

for op, filesize, cw, sw, cm, sm in product(operations, filesizes, client_workers, server_workers, client_modes, server_modes):
    print(f"Running {op} {filesize}MB | client: {cm}/{cw}, server: {sm}/{sw}")

    server_proc = subprocess.Popen([
        "python3", server,
        "--mode", sm,
        "--port", str(port+no),
        "--pool", str(sw)
    ])

    time.sleep(2)

    try:
        result = subprocess.run([
            "python3", client,    
            "--ip", ip,
            "--port", str(port+no),
            "--op", op,
            "--file", f"test_{filesize}mb.bin", 
            "--filesize", str(filesize),
            "--mode", cm,
            "--workers", str(cw)],
            capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            print("Client failed:", result.stderr)
            continue


        output = result.stdout.strip()
        parts = output.strip().split()

        if len(parts) == 8:
            cm_out, op_out, fs_out, cw_out, time_out, tp_out, success_out, fail_out = parts
            with open(output_csv, mode="a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    no,
                    op_out, fs_out,
                    cm_out, cw_out,
                    sm, sw,
                    time_out, tp_out, success_out, fail_out
                ])
        else:
            print("Unexpected output format:", output)
   
        server_proc.send_signal(signal.SIGINT)
        #server_proc.terminate()
        server_proc.wait()
        #time.sleep(5)

        no += 1

    except subprocess.TimeoutExpired:
        print("Client timed out")