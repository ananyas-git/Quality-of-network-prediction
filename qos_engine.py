"""
QoS Engine - Core prediction, popup notifications, and CSV logging
Measures network metrics, predicts streaming quality, and shows actionable advice
"""

import subprocess
import time
import csv
import os
import pickle
from datetime import datetime
import speedtest
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

try:
    from win10toast_click import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    print("win10toast_click not available - install with: pip install win10toast-click")
    TOAST_AVAILABLE = False


class QoSEngine:
    def __init__(self):
        self.model_file = 'qos_model.pkl'
        self.history_file = 'history.csv'
        self.toaster = ToastNotifier() if TOAST_AVAILABLE else None
        self.model = self._load_or_create_model()
        self._init_csv()

    def _load_or_create_model(self):
        """Load existing model or create/train a new one"""
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, 'rb') as f:
                    model = pickle.load(f)
                print("✅ Loaded existing QoS model")
                return model
            except:
                print("⚠ Error loading model, creating new one...")

        return self._create_and_train_model()

    def _create_and_train_model(self):
        """Create and train a new QoS prediction model"""
        print("🤖 Training new QoS model...")

        np.random.seed(42)
        n_samples = 1000

        latency = np.random.normal(50, 30, n_samples)
        jitter = np.random.exponential(10, n_samples)
        packet_loss = np.random.exponential(1, n_samples)
        download = np.random.normal(25, 15, n_samples)
        upload = np.random.normal(5, 3, n_samples)

        X = np.column_stack([latency, jitter, packet_loss, download, upload])

        y = []
        for i in range(n_samples):
            lat, jit, loss, down, up = X[i]

            if lat > 100 or jit > 20 or loss > 5 or down < 5:
                quality = 0  
            elif lat > 50 or jit > 10 or loss > 2 or down < 15:
                quality = 1  
            else:
                quality = 2  

            y.append(quality)

        y = np.array(y)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"✅ Model trained with {accuracy:.2%} accuracy")

        with open(self.model_file, 'wb') as f:
            pickle.dump(model, f)

        return model

    def _init_csv(self):
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'Latency_ms', 'Jitter_ms', 'PacketLoss_%',
                    'Download_Mbps', 'Upload_Mbps', 'Prediction', 'Advice'
                ])

    def measure_latency_jitter(self, host='8.8.8.8', count=10):
        try:
            result = subprocess.run(
                ['ping', '-n', str(count), host],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                times = []

                for line in lines:
                    if 'time=' in line:
                        time_part = line.split('time=')[1].split('ms')[0]
                        try:
                            times.append(float(time_part))
                        except ValueError:
                            continue

                if times:
                    latency = np.mean(times)
                    jitter = np.std(times) if len(times) > 1 else 0
                    packet_loss = 0
                    return latency, jitter, packet_loss

        except Exception as e:
            print(f"⚠ Ping error: {e}")

        return 100, 50, 10  

    def measure_speed(self):
        try:
            print("📊 Running speed test...")
            st = speedtest.Speedtest()
            st.get_best_server()

            download = st.download() / 1_000_000
            upload = st.upload() / 1_000_000

            return download, upload

        except Exception as e:
            print(f"⚠ Speed test error: {e}")
            return 10, 2

    def predict_qos(self, metrics):
        latency, jitter, packet_loss, download, upload = metrics
        features = np.array([[latency, jitter, packet_loss, download, upload]])

        prediction = self.model.predict(features)[0]
        confidence = np.max(self.model.predict_proba(features)[0])

        quality_map = {
            0: "❌ Poor Experience",
            1: "⚠ May Buffer Occasionally",
            2: "✅ Smooth Streaming"
        }

        return quality_map[prediction], confidence

    def get_advice(self, metrics, prediction):
        latency, jitter, packet_loss, download, upload = metrics

        if "Poor" in prediction:
            if latency > 100:
                return "High latency detected. Try connecting to a closer server or restart your router."
            elif packet_loss > 5:
                return "Packet loss detected. Check cable connections or contact your ISP."
            elif download < 5:
                return "Low bandwidth. Close background apps or upgrade your internet plan."
            else:
                return "Multiple issues detected. Restart your router and close unnecessary apps."

        elif "Buffer" in prediction:
            if download < 15:
                return "Lower video quality to 720p or pause other downloads."
            elif latency > 50:
                return "Moderate latency. Consider using ethernet instead of WiFi."
            else:
                return "Network is borderline. Monitor for improvements."

        else:
            return "Network looks great! Enjoy your streaming. 🎬"

    def show_popup(self, prediction, metrics, advice):
        if not TOAST_AVAILABLE:
            print(f"🔔 {prediction}")
            print(f"💡 {advice}")
            print("🔗 Dashboard: http://127.0.0.1:8050")
            return

        latency, jitter, packet_loss, download, upload = metrics

        message = f"""
🌐 {prediction}

📊 Network Metrics:
• Latency: {latency:.1f}ms | Jitter: {jitter:.1f}ms
• Loss: {packet_loss:.1f}% | Speed: {download:.1f}↓/{upload:.1f}↑ Mbps

💡 Recommendation:
{advice}

🔗 CLICK HERE TO OPEN DASHBOARD
        """.strip()

        try:
            self.toaster.show_toast(
                title="🎯 QoS Network Monitor - Click to View Dashboard",
                msg=message,
                duration=30,
                callback_on_click=self._open_dashboard,
                threaded=True
            )

            print(f"🔔 Popup shown: {prediction}")
            print("💻 Click the popup notification to open dashboard!")

        except Exception as e:
            print(f"⚠ Popup error: {e}")
            print(f"🔔 {prediction} - {advice}")

    def _open_dashboard(self):
        import webbrowser
        try:
            print("🚀 Opening dashboard in browser...")
            webbrowser.open('http://127.0.0.1:8050')
        except Exception as e:
            print("🔗 Please manually open http://127.0.0.1:8050")

    def log_to_csv(self, metrics, prediction, advice):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(self.history_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                f"{metrics[0]:.1f}",
                f"{metrics[1]:.1f}",
                f"{metrics[2]:.1f}",
                f"{metrics[3]:.1f}",
                f"{metrics[4]:.1f}",
                prediction,
                advice
            ])

    def run_qos_check(self):
        print("🔍 Running QoS check...")

        latency, jitter, packet_loss = self.measure_latency_jitter()
        download, upload = self.measure_speed()

        metrics = (latency, jitter, packet_loss, download, upload)
        prediction, confidence = self.predict_qos(metrics)
        advice = self.get_advice(metrics, prediction)

        self.show_popup(prediction, metrics, advice)
        self.log_to_csv(metrics, prediction, advice)

        print(f"✅ QoS Check Complete: {prediction} ({confidence:.0%} confidence)")
        return prediction, metrics, advice


if __name__ == "__main__":
    print("🎯 QoS Engine Test")
    engine = QoSEngine()
    prediction, metrics, advice = engine.run_qos_check()
    print("\n📋 Results:")
    print(f"  Prediction: {prediction}")
    print(f"  Metrics: {metrics}")
    print(f"  Advice: {advice}")
