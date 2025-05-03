import sys
import subprocess
from PySide2.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QHBoxLayout)
from PySide2.QtCore import QTimer, Qt
import hid

JOYCON_VENDOR_ID = 0x057E
JOYCON_PRODUCT_IDS = [0x2006, 0x2007]

class JoyConMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Joy-Con Bluetooth Manager")
        self.setFixedSize(400, 300)
        self.connected_device_address = None

        self.main_layout = QVBoxLayout()

        self.device_list = QListWidget()
        self.refresh_btn = QPushButton("🔍 Search Joy-Cons")
        self.connect_btn = QPushButton("🔗 Connect")
        self.disconnect_btn = QPushButton("❌ Disconnect")
        self.status_label = QLabel("Status: Disconnected")
        self.battery_label = QLabel("Battery: --")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)

        self.main_layout.addWidget(self.refresh_btn)
        self.main_layout.addWidget(self.device_list)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(self.battery_label)
        self.setLayout(self.main_layout)

        self.refresh_btn.clicked.connect(self.search_devices)
        self.connect_btn.clicked.connect(self.connect_device)
        self.disconnect_btn.clicked.connect(self.disconnect_device)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_battery)

    def search_devices(self):
        self.device_list.clear()
        result = subprocess.run([
            "powershell",
            "-Command",
            "Get-PnpDevice -Class Bluetooth | Where-Object { $_.FriendlyName -like '*Joy-Con*' }"
        ], capture_output=True, text=True)

        lines = result.stdout.strip().split("\n")
        for line in lines:
            if 'Joy-Con' in line:
                self.device_list.addItem(line.strip())

    def connect_device(self):
        selected = self.device_list.currentItem()
        if not selected:
            return

        line = selected.text()
        addr = "Unknown"
        # 주소 추출은 실제 시스템에 맞게 조정 필요
        self.connected_device_address = addr

        self.status_label.setText(f"Status: Ready (Assume manually paired)")
        self.timer.start(3000)

    def disconnect_device(self):
        if not self.connected_device_address:
            return

        subprocess.run([
            "powershell",
            "-Command",
            f"Remove-BluetoothDevice -DeviceAddress '{self.connected_device_address}'"
        ])

        self.status_label.setText("Status: Disconnected")
        self.battery_label.setText("Battery: --")
        self.timer.stop()
        self.connected_device_address = None

    def update_battery(self):
        try:
            for d in hid.enumerate():
                if d['vendor_id'] == JOYCON_VENDOR_ID and d['product_id'] in JOYCON_PRODUCT_IDS:
                    h = hid.device()
                    h.open_path(d['path'])
                    h.write([0x01, 0x00] + [0x00] * 48)
                    resp = h.read(64, timeout_ms=100)
                    if resp:
                        level = (resp[2] & 0xF0) >> 4
                        self.battery_label.setText(f"Battery: {level}/9")
                    h.close()
                    break
        except Exception as e:
            self.battery_label.setText("Battery: Error")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JoyConMonitor()
    window.show()
    sys.exit(app.exec_())