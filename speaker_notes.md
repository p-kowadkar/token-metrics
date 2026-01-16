# Video Demo Speaker Notes: Token Metrics Monitoring Pipeline

**Objective:** To provide a clear, concise, and professional walkthrough of the DeFi Protocol Monitoring Pipeline project, showcasing all its features and demonstrating a live alert scenario.

---

### Part 1: Introduction (0:00 - 0:45)

**(0:00 - 0:15) - Hook & Introduction**

> "Hello, my name is [Your Name], and I'm excited to present my solution for the Token Metrics take-home assignment. In the fast-paced world of DeFi, having robust, real-time monitoring isn't just a nice-to-have—it's essential for risk management and protecting assets."

**(0:15 - 0:45) - Project Goal & Overview**

> "I've built a full-stack, production-ready monitoring pipeline that tracks key protocol metrics, detects critical anomalies, and delivers instant alerts. This system is designed to be resilient, scalable, and easy to deploy. Let's dive into the architecture."

---

### Part 2: Architecture & Code Walkthrough (0:45 - 3:00)

**(0:45 - 1:30) - Architecture Overview**

> "The pipeline is built on a modern, containerized architecture. At its core, a Python service handles data ingestion from the DefiLlama API. This data, covering metrics like TVL, APY, and utilization, is stored in a PostgreSQL database."

> "A dedicated anomaly detection module analyzes this data for events like sharp TVL drops. When an anomaly is found, it's logged as an alert in the database and a notification is immediately sent via Slack."

> "The entire system is observable through a pre-configured Grafana dashboard, and a FastAPI backend exposes key data through a REST API, perfect for consumption by a mobile app or a risk engine."

**(1:30 - 3:00) - Code Highlights**

> *[Screen share VS Code or your preferred editor]*

> "Let's quickly look at the code. The project is structured for clarity and maintainability."

> **`src/pipeline.py`**: "This is the orchestrator. It runs the full sequence: fetching data, checking for anomalies, and saving the results."

> **`src/ingest.py`**: "Here, we handle all communication with the DefiLlama API. I've built in resilience with request retries and timeouts to handle network issues gracefully."

> **`src/anomaly_detector.py`**: "This is the brain of the operation. It contains the logic to identify critical events. For example, it flags a 'CRITICAL' alert if a protocol's TVL drops more than 20% in a day."

> **`setup-podman.bat`**: "For easy deployment on Windows, I've created this batch script. A key feature I implemented is the automatic loading of environment variables from a `.env` file, so there's no need to manually configure API keys or webhooks in the terminal."

---

### Part 3: Live Demonstration (3:00 - 5:30)

**(3:00 - 3:45) - Deployment with Podman**

> "Now for the fun part—let's see it in action. I'm going to start the entire stack from scratch using the Podman script."

> *[Open terminal in the project directory]*

> "First, you can see my `.env` file, which contains the Slack webhook URL. The script will pick this up automatically."

> *[Run `setup-podman.bat`]*

> "This single command creates a pod, starts the PostgreSQL database, launches the API, and brings up our Grafana instance. Everything is now running and connected."

**(3:45 - 4:30) - Exploring the Grafana Dashboard**

> *[Open browser to `http://localhost:3000`]*

> "Here is our Grafana dashboard. It provides an at-a-glance view of protocol health. We have charts visualizing Total Value Locked, APY, and Utilization Rate over time."

> "I also fixed the alert panels. The 'Recent Alerts' table now correctly queries the database, and you can see the 'Open Alerts' and 'Critical Alerts' stat cards are properly displaying counts. They are currently at zero, but we're about to change that."

**(4:30 - 5:30) - Triggering a Live Alert**

> "To simulate a real-world event, I've created a simple batch script to trigger a demo alert."

> *[Run `demo_alert.bat`]*

> "This script just inserted a critical TVL drop alert for the Aave protocol directly into our database."

> *[Switch to Slack window]*

> "And there it is! A notification just arrived in our Slack channel, detailing the protocol, the severity, and the alert message. This ensures the team can react instantly."

> *[Switch back to Grafana and refresh]*

> "If we refresh the dashboard, you can see the 'Recent Alerts' table is now populated with the new event, and our 'Open Alerts' and 'Critical Alerts' counts have both updated to one. The whole system is working end-to-end."

---

### Part 4: Conclusion (5:30 - 6:00)

**(5:30 - 6:00) - Summary & Thank You**

> "So, in just a few minutes, we've deployed a complete monitoring solution, visualized live data, and received a real-time alert via Slack. This project demonstrates a robust, scalable, and user-friendly approach to DeFi protocol monitoring."

> "Thank you for your time. I'm confident this solution meets the high standards of Token Metrics and I look forward to discussing it further."
