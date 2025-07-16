import time

import config
import machine
import network


class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False

    def connect(self):
        """Connect to WiFi network with retry logic"""
        if self.wlan.isconnected():
            self.connected = True
            return True

        print(f"Connecting to WiFi: {config.WIFI_SSID}")
        self.wlan.active(True)
        self.wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        start_time = time.time()
        while not self.wlan.isconnected():
            if time.time() - start_time > config.WIFI_TIMEOUT:
                print("WiFi connection timeout")
                self.connected = False
                return False
            time.sleep(0.5)
            print(".", end="")

        self.connected = True
        print(f"\nConnected! IP: {self.wlan.ifconfig()[0]}")
        return True

    def disconnect(self):
        """Disconnect from WiFi"""
        self.wlan.disconnect()
        self.wlan.active(False)
        self.connected = False

    def is_connected(self):
        """Check if WiFi is connected"""
        return self.wlan.isconnected()

    def get_ip(self):
        """Get current IP address"""
        if self.is_connected():
            return self.wlan.ifconfig()[0]
        return None

    def get_rssi(self):
        """Get WiFi signal strength"""
        if self.is_connected():
            return self.wlan.status('rssi')
        return None

    def reconnect(self):
        """Reconnect to WiFi if disconnected"""
        if not self.is_connected():
            print("WiFi disconnected, attempting reconnection...")
            self.disconnect()
            time.sleep(2)
            return self.connect()
        return True
