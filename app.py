from flask import Flask, request, render_template, send_file, jsonify
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os, uuid
from io import BytesIO
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Processing function (same as your original)
def process_video(video_path):
    dot_threshold = 200
    min_area = 10
    max_area = 200
    threshold_rpm = 200
    window_sec = 2

    # --- Load Video & Estimate FPS ---
    cap = cv2.VideoCapture(video_path)
    fps_meta = cap.get(cv2.CAP_PROP_FPS)
    timestamps = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ts = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        timestamps.append(ts)
    cap.release()

    fps_real = 1 / np.mean(np.diff(timestamps)) if len(timestamps) > 1 else fps_meta

    # --- Brightness Tracking ---
    cap = cv2.VideoCapture(video_path)
    brightness_list = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        roi = frame[h//3:2*h//3, w//3:2*w//3]
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(roi_gray)
        brightness_list.append(brightness)
    cap.release()

    # --- Bitstream Extraction ---
    bitstream = ""
    window_size = int(fps_real * window_sec)
    rpm_list = []
    for i in range(0, len(brightness_list)-window_size, window_size):
        segment = np.array(brightness_list[i:i+window_size])
        if len(segment) < window_size:
            break
        segment = (segment - np.mean(segment)) / np.std(segment)
        segment_fft = np.fft.fft(segment)
        freqs = np.fft.fftfreq(len(segment), d=1/fps_real)
        magnitude = np.abs(segment_fft)
        pos_freq = freqs[:len(freqs)//2]
        pos_mag = magnitude[:len(magnitude)//2]
        peak_index = np.argmax(pos_mag[1:]) + 1
        fan_rps = pos_freq[peak_index]
        fan_rpm = fan_rps * 60
        rpm_list.append(fan_rpm)
        bitstream += "1" if fan_rpm >= threshold_rpm else "0"

    # --- Decode Bitstream ---
    chunk_size = 4
    chunks = [bitstream[i:i+chunk_size] for i in range(0, len(bitstream), chunk_size)]
    secret_map = {
        "0000": "H","0001": "E","0010": "L","0011": "L",
        "0100": "O","0101": " ","0110": "W","0111": "O",
        "1000": "R","1001": "L","1010": "D","1011": "!",
        "1100": "✨","1101": "🎉","1110": "🚀","1111": "💎"
    }
    secret_message = "".join([secret_map.get(c,"?") for c in chunks])

    return brightness_list, rpm_list, fps_real, secret_message, bitstream

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "video" not in request.files:
        return jsonify({"error": "No file uploaded"})
    
    video = request.files["video"]
    if video.filename == "":
        return jsonify({"error": "No file selected"})
    
    # Validate file type
    if not video.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        return jsonify({"error": "Unsupported file format. Please upload a video file."})
    
    video_id = str(uuid.uuid4())
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}.mp4")
    video.save(video_path)

    try:
        # Run processing
        brightness_list, rpm_list, fps_real, secret_message, bitstream = process_video(video_path)
        
        if not rpm_list:
            return jsonify({"error": "Could not process the video. Please ensure it contains a visible fan."})

        # Generate analysis graphs
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Brightness over time
        axes[0, 0].plot(brightness_list, color='blue')
        axes[0, 0].set_title("Brightness Over Time (ROI)")
        axes[0, 0].set_xlabel("Frame")
        axes[0, 0].set_ylabel("Brightness")
        axes[0, 0].grid(True, alpha=0.3)
        
        # RPM over time
        axes[0, 1].plot(rpm_list, color='green')
        axes[0, 1].set_title("RPM Over Time")
        axes[0, 1].set_xlabel("Time Window")
        axes[0, 1].set_ylabel("RPM")
        axes[0, 1].grid(True, alpha=0.3)
        
        # FFT Spectrum (Full Video)
        brightness_array = np.array(brightness_list)
        fft_res = np.fft.fft(brightness_array - np.mean(brightness_array))
        freqs_full = np.fft.fftfreq(len(brightness_array), d=1/fps_real)
        mag_full = np.abs(fft_res)
        axes[1, 0].plot(freqs_full[:len(freqs_full)//2], mag_full[:len(mag_full)//2], color='red')
        axes[1, 0].set_title("FFT Spectrum (Full Video)")
        axes[1, 0].set_xlabel("Frequency (Hz)")
        axes[1, 0].set_ylabel("Magnitude")
        axes[1, 0].grid(True, alpha=0.3)
        
        # Bitstream visualization
        bitstream_display = ' '.join([bitstream[i:i+4] for i in range(0, len(bitstream), 4)])
        axes[1, 1].text(0.1, 0.5, f"Extracted Bitstream:\n{bitstream_display}", 
                       fontfamily='monospace', fontsize=10, va='center')
        axes[1, 1].set_title("Extracted Binary Data")
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        graph_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}.png")
        plt.savefig(graph_path)
        plt.close()

        result = {
            "secret_message": secret_message,
            "avg_rpm": round(float(np.mean(rpm_list)), 2),
            "bitstream": bitstream,
            "graph_url": f"/result/{video_id}.png",
            "video_id": video_id
        }
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"})

@app.route("/result/<filename>")
def result(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), mimetype="image/png")

@app.route("/download/<video_id>")
def download(video_id):
    # Create a text report
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}_report.txt")
    with open(report_path, 'w') as f:
        f.write("CPU Fan Data Exfiltration Analysis Report\n")
        f.write("=========================================\n\n")
        f.write("This report contains the analysis results of the uploaded fan video.\n")
        f.write("The system detects potential data exfiltration through fan speed modulation.\n\n")
        f.write("Results:\n")
        f.write(f"Extracted Message: {request.args.get('message', 'N/A')}\n")
        f.write(f"Average RPM: {request.args.get('rpm', 'N/A')}\n")
        f.write(f"Binary Data: {request.args.get('bits', 'N/A')}\n\n")
        f.write("Project Details:\n")
        f.write("This analysis is based on research into covert data exfiltration channels.\n")
        f.write("Malware can modulate CPU fan speeds to encode binary data, which can be \n")
        f.write("captured by external sensors like cameras and analyzed to reconstruct the data.")
    
    return send_file(report_path, as_attachment=True, download_name="fan_analysis_report.txt")

if __name__ == "__main__":
    app.run(debug=True)