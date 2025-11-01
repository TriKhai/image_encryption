import os
import math
import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from PIL import Image

# TẠO KHÓA BẰNG BẢN ĐỒ HENON
def generate_henon_key(x0, y0, a, b, length):
    """
    Sinh khóa nhị phân (bytes) độ dài 'length' bằng bản đồ hỗn loạn Henon.
    Mỗi vòng lặp sinh ra 2 byte từ giá trị x, y.
    """
    key = bytearray()
    x, y = x0, y0

    while len(key) < length:
        # Cập nhật giá trị hỗn loạn
        x_new = y + 1 - a * (x * x)
        y_new = b * x
        x, y = x_new, y_new

        # Chuyển thành byte 0–255
        val_x = int(abs(x) * 1e6) % 256
        val_y = int(abs(y) * 1e6) % 256

        key.append(val_x)
        if len(key) < length:
            key.append(val_y)

    return bytes(key)

# MÃ HÓA / GIẢI MÃ AES
def aes_encrypt(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    return cipher.encrypt(pad(data, AES.block_size))

def aes_decrypt(data, key):
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(data), AES.block_size)

# XOR ĐỘNG — CHIA NHÓM LIÊN TIẾP
def dynamic_xor(data, henon_key):
    """
    Thực hiện XOR động: mỗi nhóm dữ liệu có kích thước = henon_key[i].
    Giá trị XOR dùng chính là henon_key[i].
    """
    result = bytearray()
    key_len = len(henon_key)
    data_index = 0
    group_index = 0

    while data_index < len(data):
        i = group_index % key_len
        block_size = max(1, henon_key[i])  # tránh block_size = 0
        xor_val = henon_key[i]

        # Lấy nhóm dữ liệu và XOR từng byte trong nhóm
        block = data[data_index : data_index + block_size]
        for b in block:
            result.append(b ^ xor_val)

        # Chuyển sang nhóm kế tiếp
        data_index += block_size
        group_index += 1

    return bytes(result)

# MÃ HÓA ẢNH — KHÔNG CẦN FILE META RIÊNG
def encrypt_image(image_path, aes_key, henon_params):
    print("Bắt đầu mã hóa ảnh...")

    # Đọc dữ liệu ảnh gốc
    with Image.open(image_path) as img:
        img_bytes = img.tobytes()
        img_mode = img.mode.encode()  # mode là 'RGB', 'L:Thang độ xám,', v.v.
        img_width, img_height = img.size
    # Bước 1: AES
    aes_encrypted = aes_encrypt(img_bytes, aes_key)

    # Bước 2: Sinh khóa Henon
    henon_key = generate_henon_key(**henon_params, length=len(aes_key))

    # Bước 3: XOR động
    final_encrypted = dynamic_xor(aes_encrypted, henon_key)
    # Gói metadata vào đầu file ảnh
    header = struct.pack(
        ">HHB", img_width, img_height, len(img_mode)
    ) + img_mode + struct.pack(">Q", len(final_encrypted))

    # Ghép header + dữ liệu mã hóa
    combined = header + final_encrypted

    # Chuyển thành ảnh xám (grayscale)
    side = math.ceil(math.sqrt(len(combined)))
    padded = combined.ljust(side * side, b"\x00")
    encrypted_img = Image.frombytes("L", (side, side), padded)

    # Lưu ảnh kết quả
    out_path = f"encrypted_{os.path.splitext(os.path.basename(image_path))[0]}.png"
    encrypted_img.save(out_path)
    print(f"Đã lưu ảnh mã hóa: {out_path}")
    return out_path

# GIẢI MÃ ẢNH
def decrypt_image(encrypted_path, aes_key, henon_params):
    print("Bắt đầu giải mã ảnh...")

    # Đọc toàn bộ dữ liệu ảnh mã hóa
    with Image.open(encrypted_path) as img:
        data = bytearray(img.tobytes())

    # Giải nén header meta
    width = struct.unpack(">H", data[0:2])[0]
    height = struct.unpack(">H", data[2:4])[0]
    mode_len = data[4]
    mode_str = bytes(data[5:5 + mode_len]).decode()
    enc_data_len = struct.unpack(">Q", data[5 + mode_len:13 + mode_len])[0]

    # Dữ liệu ảnh mã hóa thực sự
    encrypted_data = bytes(data[13 + mode_len:13 + mode_len + enc_data_len])

    # Tạo lại khóa Henon
    henon_key = generate_henon_key(**henon_params, length=len(aes_key))

    # Giải XOR và AES
    aes_encrypted = dynamic_xor(encrypted_data, henon_key)
    decrypted_bytes = aes_decrypt(aes_encrypted, aes_key)

    # Tạo lại ảnh gốc
    img = Image.frombytes(mode_str, (width, height), decrypted_bytes)
    out_path = f"decrypted_{os.path.basename(encrypted_path)}"
    img.save(out_path)
    print(f"Ảnh đã giải mã: {out_path}")

# CHẠY THỬ
if __name__ == "__main__":
    AES_KEY = b"my-secret-key-16"
    HENON_PARAMS = {'x0': 0, 'y0': 0, 'a': 1.4, 'b': 0.3}
    INPUT_IMAGE = "lena.jpg"

    if not os.path.exists(INPUT_IMAGE):
        print("Không tìm thấy ảnh nguồn.")
        exit()

    encrypted = encrypt_image(INPUT_IMAGE, AES_KEY, HENON_PARAMS)
    decrypt_image(encrypted, AES_KEY, HENON_PARAMS)
