# Python WebSocket Implementation: Flask vs WebSockets

This repository contains a comparative study and performance test results for two Python WebSocket implementations: one using the `websockets` library and another with the `Flask` framework. It also includes a previously developed Discord clone app that utilizes WebSocket technology.

## Overview

The project aims to assess the performance of a WebSocket library against a framework in Python. Through meticulous research, `websockets` was chosen as a dedicated library and `Flask` as a comprehensive framework. The applications were Dockerized for testing consistency and deployment efficiency.

## Performance Evaluation

Both WebSocket implementations were benchmarked under local and cloud environments, focusing on Round-Trip Time (RTT) and CPU usage.

### Local Testing on M1 Mac (8GB RAM, Single Thread)
- **Flask-SocketIO** showed consistent RTTs with occasional spikes and varied CPU usage.
- **`websockets` library** had similar RTT ranges with higher peaks and CPU usage spikes.

### Cloud Testing on GCP (T2A-standard machine, ARM, 4GB RAM, 1vCPU)
- **Flask-SocketIO** demonstrated RTTs between 0.1663 to 0.2628 seconds and CPU usage between 5.77% and 31.32%.
- **`websockets` library** exhibited RTTs from about 0.1690 to 0.2499 seconds and CPU usage between 7.85% and 27.42%.

Flask-SocketIO provided slightly more consistent RTT performance, while the `websockets` library occasionally used less CPU. Flask-SocketIO may be preferable for applications requiring consistent low latency, whereas `websockets` might suit applications where CPU usage is a concern.

## Previous Work

The repository also includes a high-scoring Discord clone project, developed as part of a university course, which serves as a practical example of WebSocket usage.

## Contributing

Feel free to fork this project, submit issues, or send pull requests. You can contact me via egeoztas@sabanciuniv.edu for your questions and reccomendations.
