import asyncio
import time
import websockets
import psutil


async def test_websocket(uri, test_number, log_file):
    rtts = []
    async with websockets.connect(uri) as websocket:
        start_time = time.time()
        duration = 10  # Run each test for 10 seconds
        while time.time() - start_time < duration:
            msg = "ping"
            send_time = time.time()
            await websocket.send(msg)
            await websocket.recv()
            rtts.append(time.time() - send_time)
            await asyncio.sleep(1)

    average_rtt = sum(rtts) / len(rtts)
    with open(log_file, "a") as f:
        f.write(f"Test {test_number}:\nAverage RTT: {average_rtt:.4f} seconds\n")


def monitor_cpu(test_number, duration, log_file):
    cpu_usages = []
    start_time = time.time()
    while time.time() - start_time < duration:
        cpu_usages.append(psutil.cpu_percent(interval=1))

    average_cpu_usage = sum(cpu_usages) / len(cpu_usages)
    with open(log_file, "a") as f:
        f.write(f"Test {test_number}:\nAverage CPU Usage: {average_cpu_usage}%\n\n")


async def run_test(uri, test_number, duration, log_file):
    await test_websocket(uri, test_number, log_file)
    monitor_cpu(test_number, duration, log_file)


if __name__ == "__main__":
    uri = "ws://34.27.115.104:8082"
    log_file = "performance_log_websockets_gcp.txt"
    duration = 20  # Duration of each test in seconds

    for test_number in range(1, 51):
        asyncio.run(run_test(uri, test_number, duration, log_file))
