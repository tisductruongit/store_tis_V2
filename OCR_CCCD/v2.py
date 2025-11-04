"""
FILE TRÍCH XUẤT CCCD - PHIÊN BẢN TỰ ĐỘNG (v4.py)
Sử dụng YOLOv8 để phát hiện thẻ và OpenCV để tìm góc/căn chỉnh.

QUAN TRỌNG:
Code này YÊU CẦU bạn phải có file 'best.pt' - là model YOLOv8
đã được huấn luyện TÙY CHỈNH để nhận diện class 'cccd'.
Model YOLOv8 gốc KHÔNG hoạt động được.
"""

import cv2
import re
import os
import numpy as np
import torch
from PIL import Image
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from scipy.spatial import distance as dist # Dùng để sắp xếp điểm

# --- (THAY ĐỔI) ---
# Import thư viện YOLO trực tiếp từ ultralytics
from ultralytics import YOLO 

# ------------------------------------------------------------------
# KHỞI TẠO MODEL VIETOCR (Giữ nguyên)
# ------------------------------------------------------------------
def initialize_vietocr_predictor():
    print("Đang tải model VietOCR...")
    try:
        config = Cfg.load_config_from_name('vgg_transformer') 
        config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        predictor = Predictor(config)
        print(f"Model VietOCR đã sẵn sàng (Đang chạy trên: {config['device']}).")
        return predictor
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo VietOCR: {e}")
        return None

# ------------------------------------------------------------------
# KHỞI TẠO MODEL YOLOv8 (*** ĐÃ CẬP NHẬT ***)
# ------------------------------------------------------------------
def load_yolo_model(weights_path):
    """
    Tải model YOLOv8 tùy chỉnh của bạn.
    """
    print(f"Đang tải model YOLOv8 từ '{weights_path}'...")
    try:
        # API của YOLOv8 đơn giản hơn
        model = YOLO(weights_path)
        print("Model YOLOv8 đã sẵn sàng.")
        return model
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải model YOLOv8: {e}")
        print("Hãy đảm bảo bạn có file 'best.pt' (đã train bằng YOLOv8).")
        return None

# ------------------------------------------------------------------
# CÁC HÀM XỬ LÝ ẢNH VÀ OCR (Giữ nguyên)
# ------------------------------------------------------------------

def order_points(pts):
    """ Sắp xếp 4 điểm theo thứ tự: TL, TR, BR, BL """
    xSorted = pts[np.argsort(pts[:, 0]), :]
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost
    D = dist.cdist(tl[np.newaxis], rightMost)
    (br, tr) = rightMost[np.argsort(D[0])[::-1]]
    return np.array([tl, tr, br, bl], dtype="float32")

def find_card_corners(image_crop):
    """ Tìm 4 góc của thẻ trong ảnh đã được crop (bằng OpenCV) """
    gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("Lỗi OpenCV: Không tìm thấy contours.")
        return None
        
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    card_contour = contours[0]
    
    peri = cv2.arcLength(card_contour, True)
    approx = cv2.approxPolyDP(card_contour, 0.02 * peri, True)
    
    if len(approx) == 4:
        return order_points(approx.reshape(4, 2))
    else:
        print(f"Lỗi OpenCV: Tìm thấy {len(approx)} điểm, không phải 4.")
        return None

def warp_card_to_standard_size(image, corners):
    """ "Cắt" và "xoay" thẻ về một kích thước chuẩn """
    DEST_WIDTH = 1000
    DEST_HEIGHT = int(DEST_WIDTH / 1.586) # ~630

    dst_points = np.array([
        [0, 0],
        [DEST_WIDTH - 1, 0],
        [DEST_WIDTH - 1, DEST_HEIGHT - 1],
        [0, DEST_HEIGHT - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(corners, dst_points)
    warped_image = cv2.warpPerspective(image, M, (DEST_WIDTH, DEST_HEIGHT))
    return warped_image

def extract_text_from_roi(predictor, image_cv, roi):
    x, y, w, h = roi
    if w <= 0 or h <= 0: return ""
    roi_image_cv = image_cv[y:y+h, x:x+w]
    roi_image_pil = Image.fromarray(cv2.cvtColor(roi_image_cv, cv2.COLOR_BGR2RGB))
    try:
        text = predictor.predict(roi_image_pil)
        return text.strip()
    except Exception: return ""

def clean_id_number(text):
    match = re.search(r'\d{12}', text.replace(" ", ""))
    return match.group(0) if match else text
def clean_dob(text):
    match = re.search(r'(\d{2}/\d{2}/\d{4})', text.replace(" ", ""))
    return match.group(1) if match else text
def clean_name(text):
    text = re.sub(r'[^A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸY\s]', '', text)
    return ' '.join(text.split())

# ------------------------------------------------------------------
# CHƯƠNG TRÌNH CHÍNH (*** CẬP NHẬT CÁCH LẤY KẾT QUẢ ***)
# ------------------------------------------------------------------
def main():
    # === (1) CẤU HÌNH ĐƯỜNG DẪN ===
    IMAGE_PATH = '1.jpg'      # Ảnh đầu vào
    YOLO_WEIGHTS = 'yolov8n.pt'  # Model YOLOv8 tùy chỉnh của bạn
    
    # === (2) ROI CỐ ĐỊNH CHO ẢNH ĐÃ CĂN CHỈNH (1000x630) ===
    ROI_COORDINATES_WARPED = {
        "so_cccd":   (130, 125, 230, 50),
        "ho_ten":    (130, 210, 350, 55),
        "ngay_sinh": (130, 275, 200, 50),
        "que_quan":  (130, 420, 700, 50) 
    }
    
    # --- Bước 1: Khởi tạo các model ---
    if not os.path.exists(YOLO_WEIGHTS):
        print(f"LỖI: Không tìm thấy model '{YOLO_WEIGHTS}'.")
        print("Bạn cần tự huấn luyện model này bằng YOLOv8. Đang dừng...")
        return

    predictor = initialize_vietocr_predictor()
    yolo_model = load_yolo_model(YOLO_WEIGHTS)
    if predictor is None or yolo_model is None:
        print("Không thể khởi tạo model. Đang dừng...")
        return
        
    # --- Bước 2: Đọc ảnh ---
    image_cv = cv2.imread(IMAGE_PATH)
    if image_cv is None:
        print(f"Lỗi: Không thể đọc ảnh '{IMAGE_PATH}'.")
        return
    print(f"Đã đọc ảnh: {IMAGE_PATH}")

    # --- Bước 3: Phát hiện thẻ bằng YOLOv8 (*** ĐÃ CẬP NHẬT ***) ---
    # YOLOv8 cho phép set conf/iou ngay khi gọi
    results_list = yolo_model(image_cv, conf=0.5, iou=0.45) 
    
    if not results_list:
         print("Lỗi YOLOv8: Không có kết quả trả về.")
         return

    results = results_list[0] # Lấy kết quả cho ảnh đầu tiên
    
    if len(results.boxes) == 0:
        print("Lỗi YOLO: Không phát hiện thấy thẻ CCCD nào trong ảnh.")
        return

    # Lấy bounding boxes và độ tin cậy
    boxes = results.boxes.xyxy.cpu().numpy() # Lấy tọa độ [x1, y1, x2, y2]
    confs = results.boxes.conf.cpu().numpy() # Lấy độ tin cậy

    # Giả sử chỉ lấy thẻ có độ tin cậy cao nhất
    best_detection_index = np.argmax(confs)
    best_box = boxes[best_detection_index]
    x1, y1, x2, y2 = map(int, best_box)
    
    print(f"YOLOv8 đã phát hiện thẻ tại: [{x1}, {y1}, {x2}, {y2}]")

    # --- Bước 4: Crop và Tìm 4 góc bằng OpenCV (Giữ nguyên) ---
    cropped_card = image_cv[y1:y2, x1:x2]
    
    local_corners = find_card_corners(cropped_card)
    if local_corners is None:
        print("Không thể tự động tìm 4 góc. Hãy thử với ảnh rõ nét hơn.")
        return
        
    global_corners = local_corners + [x1, y1]

    # --- Bước 5: Căn chỉnh (Warp) (Giữ nguyên) ---
    warped_card_image = warp_card_to_standard_size(image_cv, global_corners)
    cv2.imwrite("warped_auto.jpg", warped_card_image) 
    print("Đã tự động căn chỉnh và lưu ảnh vào 'warped_auto.jpg'")

    # --- Bước 6: Trích xuất OCR (Giữ nguyên) ---
    print("\nBắt đầu trích xuất dữ liệu từ ảnh đã căn chỉnh...")
    extracted_data = {}
    try:
        text_id = extract_text_from_roi(predictor, warped_card_image, ROI_COORDINATES_WARPED["so_cccd"])
        extracted_data["so_cccd"] = clean_id_number(text_id)

        text_name = extract_text_from_roi(predictor, warped_card_image, ROI_COORDINATES_WARPED["ho_ten"])
        extracted_data["ho_ten"] = clean_name(text_name)

        text_dob = extract_text_from_roi(predictor, warped_card_image, ROI_COORDINATES_WARPED["ngay_sinh"])
        extracted_data["ngay_sinh"] = clean_dob(text_dob)
        
        text_hometown = extract_text_from_roi(predictor, warped_card_image, ROI_COORDINATES_WARPED["que_quan"])
        extracted_data["que_quan"] = ' '.join(text_hometown.split())
    except Exception as e:
        print(f"\nĐã xảy ra lỗi trong quá trình trích xuất: {e}")
        return

    # --- Bước 7: In kết quả (Giữ nguyên) ---
    print("\n--- KẾT QUẢ TRÍCH XUẤT (TỰ ĐỘNG - YOLOv8) ---")
    print(f"Số CCCD:   {extracted_data.get('so_cccd', 'Không tìm thấy')}")
    print(f"Họ tên:     {extracted_data.get('ho_ten', 'Không tìm thấy')}")
    print(f"Ngày sinh:  {extracted_data.get('ngay_sinh', 'Không tìm thấy')}")
    print(f"Quê quán:   {extracted_data.get('que_quan', 'Không tìm thấy')}")

if __name__ == "__main__":
    main()