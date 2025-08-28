# 📦 Intelligent Parcel Delivery System

## Overview
This project is a **Streamlit-based Intelligent Parcel Delivery & Pickup System**. It allows users to:

- Upload parcel images
- Detect QR codes
- Extract addresses using **EasyOCR**
- Generate unique parcel IDs
- Calculate delivery routes using Google Maps API (directions & geocoding)
- Display delivery route maps
- Maintain a blockchain-like hash for audit trails
- Track parcel performance metrics

---
## Interface
<img width="1912" height="859" alt="image" src="https://github.com/user-attachments/assets/cb28a92b-4061-4a83-ad5e-bd789be06209" />

## ⚡ Execution Constraints
- **Time Limit:** This project was executed **within 2 hours**.
- **Google Maps API:** I could not create an official API key within the time constraints, so I used an **unauthorized placeholder key** for demonstration purposes. As a result, geocoding and routing requests may fail or show `REQUEST_DENIED`.
- **OCR Library Choice:** I used **EasyOCR** instead of Tesseract to avoid dependency issues and ensure cross-platform compatibility without installing external binaries.

Despite these constraints, the project demonstrates a fully functional **parcel processing pipeline**, from image upload to route visualization.

---

## 🛠 Features Implemented
1. **QR Code Detection**
   - Detect and decode QR codes from parcel images.
2. **OCR Address Extraction**
   - Extract delivery address using EasyOCR with confidence scoring.
3. **Parcel ID Generation**
   - Unique parcel IDs generated with timestamp and counter.
4. **Route Calculation**
   - Demonstration of Google Maps Directions API (placeholder key used).
5. **Map Visualization**
   - Delivery and pickup locations displayed on an interactive **Folium map**.
6. **Blockchain Hash**
   - Simple hash-based audit trail for chain-of-custody verification.
7. **Performance Metrics**
   - Scan latency, route optimization time, and API response times are recorded.
8. **Streamlit Interface**
   - User-friendly interface for uploading parcels, viewing OCR results, and route visualization.

---

## 🚀 How to Run
1. Clone the repository:
   ```bash
   git clone https://github.com/Ms-vamshi/parcel-delivery-system.git
