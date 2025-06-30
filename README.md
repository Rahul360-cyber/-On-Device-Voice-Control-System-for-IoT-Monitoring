# On-Device Voice Control System for IoT Monitoring

This repository contains the complete implementation of a voice-controlled IoT monitoring system, designed to run efficiently on edge devices. The project demonstrates a full-stack approach, from training and optimizing a lightweight machine learning model with **TensorFlow Lite (TFLite)** to deploying it in a real-time application that controls an IoT data pipeline.

This project was developed as part of the "Machine Learning for IoT" course at Politecnico di Torino and serves as a practical demonstration of designing ML models for resource-constrained environments, a topic directly aligned with the research grant on "**Progettazione di modelli di machine Learning su dispositivi embedded per applicazioni industriali**."

## Key Features

-   **High-Accuracy Keyword Spotting (KWS):** A custom convolutional neural network trained to recognize "yes" and "no" voice commands with over **98.9% accuracy** on the test set.
-   **Extreme Model Optimization:** The KWS model was successfully quantized and optimized for on-device inference, resulting in a **TensorFlow Lite (`.tflite`) model under 25 KB** in size.
-   **Efficient Real-time Inference:** Achieved a **total latency reduction of over 35%** compared to a baseline CNN model, making it suitable for real-time applications on edge devices.
-   **Voice User Interface (VUI):** Deployed the TFLite model in a Python application that uses a PC's microphone to start and stop an IoT monitoring task via voice commands.
-   **Intelligent Audio Processing:** Integrated an optimized **Voice Activity Detection (VAD)** model to filter out silence and ensure the KWS model only processes active speech, saving computational resources.
-   **End-to-End IoT Data Pipeline:** The voice commands control a script that monitors PC battery status and publishes the data to a cloud broker using the **MQTT protocol**, a standard in IoT communication.

## System Architecture

The system operates in a continuous loop, demonstrating a practical edge AI workflow:

1.  **Audio Capture:** The Python script continuously records audio from a microphone.
2.  **Voice Activity Detection (VAD):** Every 0.5 seconds, the VAD model analyzes the latest audio segment to check for speech, filtering out silence to prevent unnecessary processing.
3.  **Keyword Spotting (KWS):** If speech is detected, the audio is fed into the highly optimized TFLite model for "yes/no" classification.
4.  **Action Trigger:** If a command is recognized with high confidence (>99% probability), the system toggles the state of the battery monitoring task (starts or stops it).
5.  **IoT Data Publishing:** When active, the monitoring task collects battery data and publishes it via MQTT to a remote broker.

## Core Components

### 1. Keyword Spotting (KWS) Model

-   **Task:** Classify 1-second audio clips into "yes", "no", or "unknown".
-   **Model:** A custom-designed Convolutional Neural Network (CNN).
-   **Training:** The model was trained and tested using dedicated "yes/no" datasets. The `training.ipynb` notebook contains the complete workflow.
-   **Optimization:** The final model was converted to TensorFlow Lite (`model16.tflite`) using post-training quantization to meet strict size and latency constraints.

### 2. IoT Data Communication & Storage

-   **Publisher (`publisher.py`):** A Python script that monitors PC battery level and power status. It batches data and sends it in JSON format to an MQTT broker.
-   **Subscriber (`subscriber.ipynb`):** A notebook designed to subscribe to the MQTT topic, receive the data, and store it in a Redis time-series database.
-   **REST API (`rest_server.ipynb` & `rest_client.ipynb`):** A simple RESTful API built to query the stored battery data.

## Repository Structure

```
.
├── ex1.py                  # Main Voice User Interface (VUI) application script
├── model16.tflite          # Optimized, deployable KWS model (<25 KB)
├── training.ipynb          # Notebook for KWS model training and TFLite conversion
├── preprocessing.py        # Audio preprocessing functions for the KWS model
├── ex2.py                  # Script for memory-constrained battery monitoring
├── publisher.py            # MQTT client to publish battery data
├── subscriber.ipynb        # MQTT subscriber to store data in Redis
├── rest_server.ipynb       # REST API server for managing stored data
└── rest_client.ipynb       # Client to test the REST API endpoints
```

## Getting Started

### Prerequisites

-   Python 3.8+
-   A running Redis instance (local or cloud) for data storage.
-   A microphone connected to your PC.

### Installation

1.  Clone the repository:
    ```
    git clone https://github.com/Rahul360-cyber/-On-Device-Voice-Control-System-for-IoT-Monitoring.git
    cd -On-Device-Voice-Control-System-for-IoT-Monitoring
    ```
2.  Install the required Python packages:
    ```
    pip install -r requirements.txt
    ```
    *(Note: You may need to create a `requirements.txt` file based on the libraries used, such as `tensorflow`, `pyaudio`, `paho-mqtt`, `redis`, etc.)*

### How to Run

To run the main Voice User Interface application, execute the `ex1.py` script from your terminal. You will need to provide your Redis credentials as arguments.

```
python ex1.py --device <microphone_id> --host <redis_host> --port <redis_port> --user <redis_user> --password <redis_password>
```

-   `--device`: The ID of your microphone (usually 0 or 1).
-   The script will start listening in the background. Say "yes" to start monitoring and "no" to stop.

## Technologies Used

-   **Programming:** Python
-   **Machine Learning:** TensorFlow, TensorFlow Lite, Scikit-learn
-   **IoT Protocols:** MQTT (with Paho-MQTT)
-   **Database:** Redis (Time-Series)
-   **Audio Processing:** PyAudio, Librosa
-   **Data Science:** NumPy, Pandas

```
