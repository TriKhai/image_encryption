import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from helper import encrypt_image, decrypt_image


class ImageEncryptorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Encryption System (AES + Henon + XOR)")
        self.setGeometry(100, 100, 1100, 600)

        # Các khung hiển thị ảnh
        self.original_label = QLabel("Original Image")
        self.encrypted_label = QLabel("Encrypted Image")
        self.decrypted_label = QLabel("Decrypted Image")

        for lbl in [self.original_label, self.encrypted_label, self.decrypted_label]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("border: 1px solid gray; background-color: #222; color: white;")

        # Các nút điều khiển
        self.load_btn = QPushButton("Load Image")
        self.encrypt_btn = QPushButton("Encrypt")
        self.decrypt_btn = QPushButton("Decrypt")

        self.load_btn.clicked.connect(self.load_image)
        self.encrypt_btn.clicked.connect(self.encrypt_image_ui)
        self.decrypt_btn.clicked.connect(self.decrypt_image_ui)

        # Layout
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.original_label)
        image_layout.addWidget(self.encrypted_label)
        image_layout.addWidget(self.decrypted_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.encrypt_btn)
        button_layout.addWidget(self.decrypt_btn)

        layout = QVBoxLayout()
        layout.addLayout(image_layout)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Biến dữ liệu
        self.image_path = None
        self.encrypted_path = None

        # Khóa AES và tham số Henon mặc định
        self.AES_KEY = b"my-secret-key-16"
        self.HENON_PARAMS = {'x0': 0.1, 'y0': 0.1, 'a': 1.4, 'b': 0.3}

    # ---------- Chọn ảnh ----------
    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "", "Images (*.png *.jpg *.bmp *.jpeg)"
        )
        if not file_path:
            return

        self.image_path = file_path
        self.show_image(file_path, self.original_label)
        self.statusBar().showMessage(f"Ảnh đã tải: {os.path.basename(file_path)}")

    # ---------- Mã hóa ảnh ----------
    def encrypt_image_ui(self):
        if not self.image_path:
            self._alert("Vui lòng chọn ảnh trước khi mã hóa.")
            return

        try:
            encrypted_path = encrypt_image(self.image_path, self.AES_KEY, self.HENON_PARAMS)
            self.encrypted_path = encrypted_path
            self.show_image(encrypted_path, self.encrypted_label)
            self.statusBar().showMessage(f"Mã hóa xong: {os.path.basename(encrypted_path)}")
        except Exception as e:
            self._alert(f"Lỗi khi mã hóa ảnh:\n{e}")

    # ---------- Giải mã ảnh ----------
    def decrypt_image_ui(self):
        if not self.encrypted_path or not os.path.exists(self.encrypted_path):
            self._alert("Không tìm thấy ảnh mã hóa để giải mã.")
            return

        try:
            decrypt_image(self.encrypted_path, self.AES_KEY, self.HENON_PARAMS)
            decrypted_path = f"decrypted_{os.path.basename(self.encrypted_path)}"
            self.show_image(decrypted_path, self.decrypted_label)
            self.statusBar().showMessage(f"Giải mã xong: {os.path.basename(decrypted_path)}")
        except Exception as e:
            self._alert(f"Lỗi khi giải mã ảnh:\n{e}")

    # ---------- Hiển thị ảnh ----------
    def show_image(self, path, label):
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(350, 350, Qt.KeepAspectRatio)
        label.setPixmap(pixmap)

    # ---------- Thông báo ----------
    def _alert(self, message):
        QMessageBox.warning(self, "Thông báo", message)
        self.statusBar().showMessage(message)


def main():
    app = QApplication(sys.argv)
    window = ImageEncryptorApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
