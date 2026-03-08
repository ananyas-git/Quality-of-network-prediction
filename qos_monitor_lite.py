"""
QoS Monitor Lite - Automatic streaming detection and QoS monitoring
Runs in background, detects streaming traffic, triggers QoS predictions
Now with enhanced popup options!
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from qos_engine import QoSEngine

# Import enhanced popup if available
try:
    from enhanced_popup import EnhancedPopup
    ENHANCED_POPUP_AVAILABLE = True
    print("✅ Enhanced popup system available")
except ImportError:
    ENHANCED_POPUP_AVAILABLE = False
    print("ℹ️ Using standard popup system")


class StreamingDetector:
    def __init__(self):
        self.streaming_domains = {
            'youtube.com', 'youtu.be', 'googlevideo.com',
            'netflix.com', 'nflxvideo.net', 'nflxso.net',
            'twitch.tv', 'ttvnw.net',
            'hulu.com', 'hulustream.com', '1e100.net',
            'amazon.com', 'amazonvideo.com',
            'disneyplus.com', 'disney-plus.net',
            'hbo.com', 'hbogo.com', 'hbomax.com', 'chrome.com',
            'spotify.com', 'scdn.co',
            'apple.com',
            'facebook.com', 'fbcdn.net',
            'vimeo.com', 'vimeocdn.com',
            'dailymotion.com', 'dmcdn.net',
            'crunchyroll.com'
        }

        self.streaming_processes = {
            'chrome.exe', 'firefox.exe', 'msedge.exe', 'opera.exe',
            'netflix.exe', 'spotify.exe', 'vlc.exe', 'potplayer.exe',
            'obs32.exe', 'obs64.exe', 'streamlabs obs.exe'
        }

        self.last_streaming_check = datetime.now()
        self.streaming_cooldown = timedelta(seconds=30)

    def get_active_connections(self):
        """Get all active network connections"""
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    connections.append({
                        'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}",
                        'pid': conn.pid,
                        'status': conn.status
                    })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return connections

    def is_streaming_domain(self, ip):
        """Check if IP might belong to streaming services"""
        try:
            import socket
            hostname = socket.gethostbyaddr(ip)[0].lower()
            return any(domain in hostname for domain in self.streaming_domains)
        except:
            return False

    def get_process_name(self, pid):
        """Get process name from PID"""
        try:
            if pid:
                process = psutil.Process(pid)
                return process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None

    def detect_streaming_activity(self):
        """Detect if streaming is currently active"""
        connections = self.get_active_connections()
        streaming_indicators = []

        for conn in connections:
            process_name = self.get_process_name(conn['pid'])
            if process_name and any(proc in process_name for proc in self.streaming_processes):
                streaming_indicators.append(f"Process: {process_name}")

            remote_ip = conn['remote_addr'].split(':')[0]
            if self.is_streaming_domain(remote_ip):
                streaming_indicators.append(f"Domain: {remote_ip}")

        net_io = psutil.net_io_counters()
        if hasattr(self, 'last_net_io'):
            bytes_sent = net_io.bytes_sent - self.last_net_io.bytes_sent
            bytes_recv = net_io.bytes_recv - self.last_net_io.bytes_recv

            if bytes_recv > 1_000_000:
                streaming_indicators.append("High bandwidth usage detected")

        self.last_net_io = net_io
        return streaming_indicators

    def should_run_qos_check(self):
        """Determine if we should run a QoS check"""
        if datetime.now() - self.last_streaming_check < self.streaming_cooldown:
            return False

        streaming_activity = self.detect_streaming_activity()
        return len(streaming_activity) > 0


class QoSMonitor:
    def __init__(self, use_enhanced_popup=True):
        self.detector = StreamingDetector()
        self.qos_engine = QoSEngine()
        self.running = False
        self.check_interval = 10

        if use_enhanced_popup and ENHANCED_POPUP_AVAILABLE:
            self.enhanced_popup = EnhancedPopup()
            print("🎨 Using enhanced popup with buttons")
        else:
            self.enhanced_popup = None
            print("📱 Using standard notification popup")

    def start_monitoring(self):
        """Start background monitoring"""
        self.running = True
        print("🎯 QoS Monitor started - detecting streaming activity...")
        print(f"⏰ Checking every {self.check_interval} seconds")

        if self.enhanced_popup:
            print("🔘 Enhanced popups: Click 'Open Dashboard' button")
        else:
            print("📱 Standard popups: Click notification to open dashboard")

        print("🛑 Press Ctrl+C to stop\n")

        try:
            while self.running:
                self._monitoring_loop()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopping QoS Monitor...")
            self.running = False

    def _monitoring_loop(self):
        """Single monitoring iteration"""
        try:
            streaming_activity = self.detector.detect_streaming_activity()

            if streaming_activity:
                print(f"🎬 Streaming detected: {', '.join(streaming_activity[:2])}")

                if self.detector.should_run_qos_check():
                    print("🔍 Running QoS check...")
                    self.detector.last_streaming_check = datetime.now()
                    thread = threading.Thread(target=self._run_qos_check)
                    thread.daemon = True
                    thread.start()
                else:
                    print("⏳ QoS check on cooldown...")
            else:
                print("📶 No streaming activity detected")

        except Exception as e:
            print(f"⚠️ Monitoring error: {e}")

    def _run_qos_check(self):
        """Run QoS check in background thread"""
        try:
            latency, jitter, packet_loss = self.qos_engine.measure_latency_jitter()
            download, upload = self.qos_engine.measure_speed()
            metrics = (latency, jitter, packet_loss, download, upload)

            prediction, confidence = self.qos_engine.predict_qos(metrics)
            advice = self.qos_engine.get_advice(metrics, prediction)

            if self.enhanced_popup:
                self.enhanced_popup.show_popup_with_buttons(prediction, metrics, advice)
            else:
                self.qos_engine.show_popup(prediction, metrics, advice)

            self.qos_engine.log_to_csv(metrics, prediction, advice)

            print(f"✅ QoS Result: {prediction} ({confidence:.0%} confidence)")

        except Exception as e:
            print(f"⚠️ QoS check error: {e}")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False


class QoSTrayApp:
    def __init__(self, use_enhanced_popup=True):
        self.monitor = QoSMonitor(use_enhanced_popup)

    def create_tray_icon(self):
        """Create system tray icon"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            def create_icon():
                width = height = 32
                image = Image.new('RGB', (width, height), 'blue')
                draw = ImageDraw.Draw(image)
                draw.ellipse([8, 8, 24, 24], fill='white')
                return image

            icon = pystray.Icon(
                "QoS Monitor",
                create_icon(),
                menu=pystray.Menu(
                    pystray.MenuItem("Open Dashboard", self._open_dashboard),
                    pystray.MenuItem("Start Monitoring", self._start_monitoring),
                    pystray.MenuItem("Stop Monitoring", self._stop_monitoring),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Exit", self._quit_app)
                )
            )
            return icon

        except ImportError:
            print("⚠️ pystray not available - install with: pip install pystray pillow")
            return None

    def _open_dashboard(self, icon=None, item=None):
        import webbrowser
        webbrowser.open('http://127.0.0.1:8050')

    def _start_monitoring(self, icon=None, item=None):
        if not self.monitor.running:
            thread = threading.Thread(target=self.monitor.start_monitoring)
            thread.daemon = True
            thread.start()

    def _stop_monitoring(self, icon=None, item=None):
        self.monitor.stop_monitoring()

    def _quit_app(self, icon=None, item=None):
        self.monitor.stop_monitoring()
        if icon:
            icon.stop()


def main():
    """Main entry point"""
    import sys

    use_enhanced_popup = True
    tray_mode = False

    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == '--tray':
                tray_mode = True
            elif arg == '--standard-popup':
                use_enhanced_popup = False

    print("🎯 QoS Monitor Lite v2.0")
    print("=" * 40)

    if tray_mode:
        print("🔧 Starting in system tray mode...")
        tray_app = QoSTrayApp(use_enhanced_popup)
        icon = tray_app.create_tray_icon()

        if icon:
            tray_app._start_monitoring()
            icon.run()
        else:
            print(" Could not create tray icon, falling back to console mode")
            monitor = QoSMonitor(use_enhanced_popup)
            monitor.start_monitoring()
    else:
        monitor = QoSMonitor(use_enhanced_popup)
        monitor.start_monitoring()


if __name__ == "__main__":
    print("🎯 QoS Monitor Lite v2.0")
    print("=" * 40)
    main()
