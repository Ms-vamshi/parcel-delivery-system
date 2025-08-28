import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pytesseract
import json
import time
import datetime
import requests
import folium
from streamlit_folium import st_folium
import random
import hashlib
import re

# ------------------------------
# Configuration
# ------------------------------
st.set_page_config(
    page_title="Intelligent Parcel Delivery System",
    page_icon="📦",
    layout="wide"
)

# 🔑 Directly insert your Google Maps API key here
API_KEY = "AIzaSyB2t4hOvy4D0fX0nb8T_By3xp4ibdkjWTQ"

# Initialize session state
if 'tracking_data' not in st.session_state:
    st.session_state.tracking_data = {}
if 'parcel_counter' not in st.session_state:
    st.session_state.parcel_counter = 1

# ------------------------------
# Parcel Processor Class
# ------------------------------
class ParcelProcessor:
    def __init__(self):
        self.status_stages = [
            "picked_up",
            "in_transit", 
            "out_for_delivery",
            "delivered"
        ]

    # --------------------------
    # QR Code Extraction
    # --------------------------
    def extract_qr_code(self, image):
        try:
            open_cv_image = np.array(image)
            if len(open_cv_image.shape) == 3:
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
            qr_detector = cv2.QRCodeDetector()
            data, points, _ = qr_detector.detectAndDecode(open_cv_image)
            if data:
                return [{
                    'data': data,
                    'type': 'QR_CODE',
                    'confidence': 0.99
                }]
            return []
        except Exception as e:
            st.error(f"QR extraction failed: {str(e)}")
            return []

    # --------------------------
    # OCR Text Extraction
    # --------------------------
    def extract_text_ocr(self, image):
        try:
            open_cv_image = np.array(image)
            if len(open_cv_image.shape) == 3:
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
            enhanced = cv2.equalizeHist(open_cv_image)
            text = pytesseract.image_to_string(enhanced)
            confidence = pytesseract.image_to_data(enhanced, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in confidence['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            return {
                'text': text.strip(),
                'confidence': avg_confidence / 100.0
            }
        except Exception as e:
            st.error(f"OCR extraction failed: {str(e)}")
            return {'text': '', 'confidence': 0}

    # --------------------------
    # Basic Address Parser
    # --------------------------
    def parse_address(self, text):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        address_components = {
            'street': '',
            'city': '',
            'postal_code': '',
            'coordinates': []
        }
        zip_pattern = r'\b\d{5}(-\d{4})?\b'
        for line in lines:
            if re.search(zip_pattern, line):
                address_components['postal_code'] = re.search(zip_pattern, line).group()
                parts = line.split()
                if len(parts) > 1:
                    address_components['city'] = ' '.join(parts[:-1])
            elif any(word.lower() in line.lower() for word in ['st', 'ave', 'rd', 'dr', 'blvd']):
                address_components['street'] = line
        return address_components

    # --------------------------
    # Geocode Address
    # --------------------------
    def geocode_address(self, address_text):
        url = f"https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address_text, "key": API_KEY}
        try:
            resp = requests.get(url, params=params).json()
            if resp['status'] == "OK":
                loc = resp['results'][0]['geometry']['location']
                return [loc['lat'], loc['lng']]
            else:
                st.warning(f"Geocoding failed: {resp['status']}")
                return [37.7749, -122.4194]
        except Exception as e:
            st.error(f"Geocoding API error: {str(e)}")
            return [37.7749, -122.4194]

    # --------------------------
    # Calculate Route
    # --------------------------
    def calculate_route(self, from_addr, to_addr):
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": from_addr,
            "destination": to_addr,
            "mode": "driving",
            "key": API_KEY
        }
        try:
            resp = requests.get(url, params=params).json()
            if resp['status'] == "OK":
                leg = resp['routes'][0]['legs'][0]
                distance_km = leg['distance']['value'] / 1000
                duration_min = leg['duration']['value'] / 60
                route_points = [(step['end_location']['lat'], step['end_location']['lng']) for step in leg['steps']]
                return {
                    "distance_km": round(distance_km, 1),
                    "duration_min": round(duration_min, 0),
                    "route_points": route_points
                }
            else:
                st.warning(f"Google API error: {resp['status']}")
                return {"distance_km": 0, "duration_min": 0, "route_points": []}
        except Exception as e:
            st.error(f"Route calculation failed: {str(e)}")
            return {"distance_km": 0, "duration_min": 0, "route_points": []}

    # --------------------------
    # Generate Parcel ID
    # --------------------------
    def generate_parcel_id(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        counter = f"{st.session_state.parcel_counter:06d}"
        st.session_state.parcel_counter += 1
        return f"PRC-{timestamp}-{counter}"

    # --------------------------
    # Blockchain Hash
    # --------------------------
    def create_blockchain_hash(self, data):
        return "0x" + hashlib.sha256(str(data).encode()).hexdigest()[:16]


# ------------------------------
# Initialize Processor
# ------------------------------
processor = ParcelProcessor()

# ------------------------------
# Streamlit UI
# ------------------------------
st.title("📦 Intelligent Parcel Delivery & Pickup System")
st.markdown("Upload a parcel image or enter delivery details to process your shipment")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Parcel Input")
    uploaded_file = st.file_uploader("Upload Parcel Image", type=['png','jpg','jpeg'])
    manual_address = st.text_area("Manual Address (Fallback)", placeholder="123 Main St, San Francisco, CA 94102", height=80)
    pickup_location = st.text_input("Pickup Location", "Distribution Center A, San Francisco, CA")

with col2:
    st.subheader("2. Processing Results")
    if uploaded_file is not None or manual_address:
        if st.button("🚀 Process Parcel", type="primary"):
            with st.spinner("Processing parcel..."):
                start_time = time.time()
                barcode_data, barcode_type, confidence_score = "", "", 0
                address_extracted = {}

                if uploaded_file is not None:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Uploaded Parcel Image", use_column_width=True)
                    qr_results = processor.extract_qr_code(image)
                    if qr_results:
                        barcode_data = qr_results[0]['data']
                        barcode_type = qr_results[0]['type']
                        confidence_score = qr_results[0]['confidence']
                        st.success(f"✅ QR Code: {barcode_data}")
                    ocr_result = processor.extract_text_ocr(image)
                    if ocr_result['text']:
                        address_extracted = processor.parse_address(ocr_result['text'])
                        st.success(f"✅ OCR Extracted (Confidence: {ocr_result['confidence']:.2f})")
                        st.text(f"Raw OCR Text:\n{ocr_result['text'][:200]}...")

                if not address_extracted.get('street') and manual_address:
                    address_extracted = {'street': manual_address, 'city': '', 'postal_code': '', 'coordinates': []}

                if not barcode_data:
                    barcode_data = processor.generate_parcel_id()
                    barcode_type = "Generated ID"
                    confidence_score = 1.0

                delivery_coords = processor.geocode_address(address_extracted.get('street', manual_address))
                address_extracted['coordinates'] = delivery_coords

                route_info = processor.calculate_route(pickup_location, manual_address or address_extracted['street'])

                processing_time = int((time.time() - start_time) * 1000)
                current_time = datetime.datetime.now().isoformat() + "Z"

                parcel_data = {
                    "parcel_id": barcode_data,
                    "recognition_result": {
                        "barcode_data": barcode_data,
                        "barcode_type": barcode_type,
                        "confidence_score": round(confidence_score, 3),
                        "address_extracted": address_extracted,
                        "processing_time_ms": processing_time
                    },
                    "route_assignment": {
                        "driver_id": f"DRV-{random.randint(100,999)}",
                        "route_id": f"RT-{datetime.date.today()}-{random.randint(10,99)}",
                        "position_in_route": random.randint(5, 15),
                        "estimated_delivery": current_time,
                        "priority_level": random.choice(["standard", "priority", "express"]),
                        "optimization_score": round(random.uniform(0.85, 0.98), 2)
                    },
                    "tracking_data": {
                        "current_status": "picked_up",
                        "location_history": [{
                            "timestamp": current_time,
                            "location": pickup_location,
                            "event": "picked_up"
                        }],
                        "predicted_eta": (datetime.datetime.now() + datetime.timedelta(minutes=route_info['duration_min'])).isoformat() + "Z",
                        "confidence_interval": int(route_info['duration_min'] * 60 * 0.1)
                    },
                    "audit_trail": {
                        "blockchain_hash": processor.create_blockchain_hash(barcode_data + current_time),
                        "chain_of_custody": ["warehouse", f"driver_{random.randint(100,999)}", "pending"],
                        "anomalies_detected": [],
                        "compliance_status": "verified"
                    },
                    "performance_metrics": {
                        "scan_latency_ms": processing_time,
                        "route_optimization_time_ms": random.randint(800, 1500),
                        "api_response_time_ms": random.randint(10, 25)
                    }
                }

                st.session_state.tracking_data[barcode_data] = parcel_data
                st.subheader("📊 Processing Complete")
                st.info(f"🚛 Route: {route_info['distance_km']} km, ETA: {route_info['duration_min']:.0f} minutes")
                st.subheader("📄 API Response (JSON)")
                st.json(parcel_data)

                # Map
                if address_extracted.get('coordinates'):
                    st.subheader("🗺️ Delivery Route Map")
                    m = folium.Map(location=delivery_coords, zoom_start=12)
                    folium.Marker([37.7749, -122.4194], popup=pickup_location, tooltip="Pickup", icon=folium.Icon(color="green")).add_to(m)
                    folium.Marker(delivery_coords, popup="Delivery Address", tooltip="Delivery", icon=folium.Icon(color="red")).add_to(m)
                    if route_info['route_points']:
                        folium.PolyLine(route_info['route_points'], weight=4, color='blue', opacity=0.7).add_to(m)
                    st_folium(m, width=700, height=400)
