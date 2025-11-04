"""
FILE TRÍCH XUẤT THÔNG TIN CCCD SỬ DỤNG VIETOCR (v1.py)

Đã cập nhật tọa độ ROI ước tính cho file '1.jpg' (kích thước 1280x960).
"""

import cv2
import re
import os
from PIL import Image  # Thư viện VietOCR cần
import torch              
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

# ------------------------------------------------------------------
# KHỞI TẠO MODEL VIETOCR (CHỈ LÀM 1 LẦN)
# ------------------------------------------------------------------

def initialize_vietocr_predictor():
    """
    Tải model VietOCR vào bộ nhớ.
    Tự động dùng GPU (CUDA) nếu có, nếu không thì dùng CPU.
    """
    print("Đang tải model VietOCR (chỉ chạy 1 lần đầu tiên)...")
    
    try:
        # 1. Tải cấu hình
        config = Cfg.load_config_from_name('vgg_transformer') 
        
        # 2. Cấu hình thiết bị (GPU nếu có)
        config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        
        # 3. Khởi tạo Predictor
        # Thư viện sẽ tự động tải file weights mặc định về
        # thư mục cache (ví dụ: ~/.vietocr) trong lần chạy đầu tiên.
        predictor = Predictor(config)
        
        print(f"Model VietOCR đã sẵn sàng (Đang chạy trên: {config['device']}).")
        return predictor

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo VietOCR: {e}")
        print("Vui lòng kiểm tra cài đặt PyTorch, CUDA (nếu có) và kết nối internet (cho lần tải đầu).")
        return None

# ------------------------------------------------------------------
# CÁC HÀM TIỆN ÍCH (TRÍCH XUẤT VÀ DỌN DẸP)
# ------------------------------------------------------------------

def extract_text_from_roi(predictor, image_cv, roi):
    """
    Cắt ảnh theo ROI (OpenCV) và trích xuất text dùng VietOCR.
    predictor: Đối tượng predictor đã được khởi tạo
    image_cv: Ảnh gốc đọc bằng OpenCV
    roi: (x, y, w, h) - Tọa độ vùng cần đọc
    """
    x, y, w, h = roi
    
    if w <= 0 or h <= 0:
        print(f"Lỗi: ROI {roi} không hợp lệ.")
        return ""
        
    roi_image_cv = image_cv[y:y+h, x:x+w]
    roi_image_pil = Image.fromarray(cv2.cvtColor(roi_image_cv, cv2.COLOR_BGR2RGB))
    
    try:
        text = predictor.predict(roi_image_pil)
        return text.strip()
    except Exception as e:
        print(f"Lỗi khi dự đoán text cho ROI {roi}: {e}")
        return ""

def clean_id_number(text):
    """Tìm chuỗi 12 chữ số liên tục."""
    text_no_spaces = text.replace(" ", "")
    match = re.search(r'\d{12}', text_no_spaces)
    return match.group(0) if match else text

def clean_dob(text):
    """Tìm ngày tháng theo định dạng dd/mm/yyyy."""
    text_no_spaces = text.replace(" ", "")
    match = re.search(r'(\d{2}/\d{2}/\d{4})', text_no_spaces)
    return match.group(1) if match else text

def clean_name(text):
    """Lọc tên (thường là IN HOA)."""
    text = re.sub(r'[^A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ\s]', '', text)
    return ' '.join(text.split())

# ------------------------------------------------------------------
# CHƯƠNG TRÌNH CHÍNH
# ------------------------------------------------------------------

def main():
    # === (1) ĐƯỜNG DẪN ẢNH ===
    IMAGE_PATH = '1.jpg'  # <<< CẬP NHẬT TÊN FILE ẢNH CỦA BẠN
    
    # === (2) TỌA ĐỘ ROI ƯỚC TÍNH CHO ẢNH '1.jpg' (1280x960) ===
    # (x, y, w, h)
    ROI_COORDINATES = {
        # Số CCCD: 037094012351
        "so_cccd":   (435, 340, 300, 45),

        # Họ và tên: TRỊNH QUANG DUY
        "ho_ten":    (435, 410, 400, 50),

        # Ngày sinh: 04/09/1994
        "ngay_sinh": (435, 470, 200, 50),
        
        # Quê quán: Tân Thành, Kim Sơn, Ninh Bình
        "que_quan":  (435, 595, 600, 55)
    }

    # --- Bước 1: Khởi tạo model ---
    predictor = initialize_vietocr_predictor()
    if predictor is None:
        return

    # --- Bước 2: Đọc ảnh ---
    if not os.path.exists(IMAGE_PATH):
        print(f"Lỗi: Không tìm thấy file ảnh tại '{IMAGE_PATH}'")
        return

    image_cv = cv2.imread(IMAGE_PATH)
    if image_cv is None:
        print(f"Lỗi: Không thể đọc file ảnh '{IMAGE_PATH}'.")
        return

    print(f"Đã đọc ảnh: {IMAGE_PATH} (Kích thước: {image_cv.shape[1]}x{image_cv.shape[0]})")
    print("\nBắt đầu trích xuất dữ liệu...")

    # --- Bước 3: Trích xuất từng vùng ---
    extracted_data = {}
    try:
        roi_id = ROI_COORDINATES["so_cccd"]
        text_id = extract_text_from_roi(predictor, image_cv, roi_id)
        extracted_data["so_cccd"] = clean_id_number(text_id)

        roi_name = ROI_COORDINATES["ho_ten"]
        text_name = extract_text_from_roi(predictor, image_cv, roi_name)
        extracted_data["ho_ten"] = clean_name(text_name)

        roi_dob = ROI_COORDINATES["ngay_sinh"]
        text_dob = extract_text_from_roi(predictor, image_cv, roi_dob)
        extracted_data["ngay_sinh"] = clean_dob(text_dob)
        
        roi_hometown = ROI_COORDINATES["que_quan"]
        text_hometown = extract_text_from_roi(predictor, image_cv, roi_hometown)
        extracted_data["que_quan"] = ' '.join(text_hometown.split())

    except KeyError as e:
        print(f"Lỗi: Không tìm thấy key '{e}' trong ROI_COORDINATES.")
        return
    except Exception as e:
        print(f"\nĐã xảy ra lỗi trong quá trình trích xuất: {e}")
        return

    # --- Bước 4: In kết quả ---
    print("\n--- KẾT QUẢ TRÍCH XUẤT (VIETOCR) ---")
    print(f"Số CCCD:   {extracted_data.get('so_cccd', 'Không tìm thấy')}")
    print(f"Họ tên:     {extracted_data.get('ho_ten', 'Không tìm thấy')}")
    print(f"Ngày sinh:  {extracted_data.get('ngay_sinh', 'Không tìm thấy')}")
    print(f"Quê quán:   {extracted_data.get('que_quan', 'Không tìm thấy')}")

if __name__ == "__main__":
    main()