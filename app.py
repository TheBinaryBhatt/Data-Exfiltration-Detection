from flask import Flask, request, render_template, send_file, jsonify, session
from flask_session import Session
import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import os, uuid, json
from io import BytesIO
import base64
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import tempfile
from datetime import datetime
import plotly
import plotly.express as px
import plotly.graph_objects as go
import json as jsonlib
from ml_model.model import train_anomaly_detector, detect_anomalies

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'session' 
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
Session(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the ML model
anomaly_model, scaler = train_anomaly_detector()

def process_video(video_path):
    # Configuration
    threshold_rpm = 200
    window_sec = 2

    # Load Video & Estimate FPS
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

    # Brightness Tracking
    cap = cv2.VideoCapture(video_path)
    brightness_list = []
    frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        roi = frame[h//3:2*h//3, w//3:2*w//3]
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(roi_gray)
        brightness_list.append(brightness)
        frames.append(frame)
    
    cap.release()

    # Bitstream Extraction
    bitstream = ""
    window_size = int(fps_real * window_sec)
    rpm_list = []
    timestamps = []
    
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
        timestamps.append(i / fps_real)
        bitstream += "1" if fan_rpm >= threshold_rpm else "0"

    # Anomaly Detection
    anomalies, anomaly_scores = detect_anomalies(anomaly_model, scaler, rpm_list)

    # Decode Bitstream
    chunk_size = 4
    chunks = [bitstream[i:i+chunk_size] for i in range(0, len(bitstream), chunk_size)]
    secret_map = {
        "0000": "H", "0001": "E", "0010": "L", "0011": "L",
        "0100": "O", "0101": " ", "0110": "W", "0111": "O",
        "1000": "R", "1001": "L", "1010": "D", "1011": "!",
        "1100": "✨", "1101": "🎉", "1110": "🚀", "1111": "💎"
    }
    secret_message = "".join([secret_map.get(c, "?") for c in chunks])

    return {
        'brightness': brightness_list,
        'rpm': rpm_list,
        'timestamps': timestamps,
        'fps': fps_real,
        'message': secret_message,
        'bitstream': bitstream,
        'anomalies': anomalies,
        'anomaly_scores': anomaly_scores,
        'frames_count': len(frames)
    }

def generate_interactive_plots(results, video_id):
    # Create interactive RPM plot with anomalies
    rpm_df = pd.DataFrame({
        'Time': results['timestamps'],
        'RPM': results['rpm'],
        'Anomaly': results['anomalies'],
        'Score': results['anomaly_scores']
    })
    
    fig_rpm = go.Figure()
    
    # Add RPM trace
    fig_rpm.add_trace(go.Scatter(
        x=rpm_df['Time'], 
        y=rpm_df['RPM'],
        mode='lines+markers',
        name='RPM',
        line=dict(color='blue'),
        marker=dict(size=6)
    ))
    
    # Add anomaly points
    anomalies = rpm_df[rpm_df['Anomaly'] == -1]
    if not anomalies.empty:
        fig_rpm.add_trace(go.Scatter(
            x=anomalies['Time'],
            y=anomalies['RPM'],
            mode='markers',
            name='Anomaly',
            marker=dict(color='red', size=10, symbol='x'),
            hovertemplate='<b>Anomaly Detected</b><br>Time: %{x:.2f}s<br>RPM: %{y}<extra></extra>'
        ))
    
    fig_rpm.update_layout(
        title='Fan RPM Over Time with Anomaly Detection',
        xaxis_title='Time (seconds)',
        yaxis_title='RPM',
        hovermode='closest',
        showlegend=True
    )
    
    # Create brightness plot
    brightness_df = pd.DataFrame({
        'Frame': range(len(results['brightness'])),
        'Brightness': results['brightness']
    })
    
    fig_brightness = px.line(brightness_df, x='Frame', y='Brightness', 
                            title='Brightness Variation Over Frames')
    fig_brightness.update_layout(
        xaxis_title='Frame Number',
        yaxis_title='Brightness (0-255)'
    )
    
    # Create FFT plot
    brightness_array = np.array(results['brightness'])
    fft_res = np.fft.fft(brightness_array - np.mean(brightness_array))
    freqs_full = np.fft.fftfreq(len(brightness_array), d=1/results['fps'])
    mag_full = np.abs(fft_res)
    
    fft_df = pd.DataFrame({
        'Frequency': freqs_full[:len(freqs_full)//2],
        'Magnitude': mag_full[:len(mag_full)//2]
    })
    
    fig_fft = px.line(fft_df, x='Frequency', y='Magnitude', 
                     title='FFT Spectrum of Brightness Signal')
    fig_fft.update_layout(
        xaxis_title='Frequency (Hz)',
        yaxis_title='Magnitude'
    )
    
    # Convert plots to JSON
    plot_rpm = jsonlib.dumps(fig_rpm, cls=plotly.utils.PlotlyJSONEncoder)
    plot_brightness = jsonlib.dumps(fig_brightness, cls=plotly.utils.PlotlyJSONEncoder)
    plot_fft = jsonlib.dumps(fig_fft, cls=plotly.utils.PlotlyJSONEncoder)
    
    return plot_rpm, plot_brightness, plot_fft

def generate_pdf_report(results, video_id, plot_paths):
    """Generate a professional PDF report"""
    report_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}_report.pdf")
    
    # Create PDF
    c = canvas.Canvas(report_path, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "CPU Fan Data Exfiltration Analysis Report")
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, "Analysis Summary:")
    c.setFont("Helvetica", 10)
    
    y_pos = height - 120
    c.drawString(50, y_pos, f"Extracted Message: {results['message']}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Average RPM: {np.mean(results['rpm']):.2f}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Anomalies Detected: {sum(1 for a in results['anomalies'] if a == -1)}")
    y_pos -= 20
    c.drawString(50, y_pos, f"Binary Data: {results['bitstream']}")
    
    # Add plots
    y_pos -= 40
    for i, plot_path in enumerate(plot_paths):
        if os.path.exists(plot_path):
            c.drawString(50, y_pos, f"Analysis Graph {i+1}:")
            y_pos -= 20
            c.drawImage(plot_path, 50, y_pos - 150, width=500, height=150)
            y_pos -= 180
            if y_pos < 100:
                c.showPage()
                y_pos = height - 50
    
    # Add technical details
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_pos, "Technical Details:")
    c.setFont("Helvetica", 10)
    y_pos -= 20
    c.drawString(50, y_pos, "This analysis detects potential data exfiltration through CPU fan speed modulation.")
    y_pos -= 15
    c.drawString(50, y_pos, "Malware can encode binary data in fan RPM variations, which can be captured")
    y_pos -= 15
    c.drawString(50, y_pos, "by cameras and analyzed using FFT-based frequency analysis.")
    
    c.save()
    return report_path

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
        results = process_video(video_path)
        
        if not results['rpm']:
            return jsonify({"error": "Could not process the video. Please ensure it contains a visible fan."})

        # Generate interactive plots
        plot_rpm, plot_brightness, plot_fft = generate_interactive_plots(results, video_id)
        
        # Store results in session
        session['last_analysis'] = {
            'video_id': video_id,
            'results': results
        }

        response = {
            "success": True,
            "secret_message": results['message'],
            "avg_rpm": round(float(np.mean(results['rpm'])), 2),
            "anomaly_count": sum(1 for a in results['anomalies'] if a == -1),
            "bitstream": results['bitstream'],
            "plot_rpm": plot_rpm,
            "plot_brightness": plot_brightness,
            "plot_fft": plot_fft,
            "video_id": video_id
        }
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"})

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """REST API endpoint for programmatic access"""
    if "video" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    video = request.files["video"]
    if video.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    video_id = str(uuid.uuid4())
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}.mp4")
    video.save(video_path)

    try:
        results = process_video(video_path)
        
        if not results['rpm']:
            return jsonify({"error": "Could not process the video"}), 400

        return jsonify({
            "message": results['message'],
            "avg_rpm": round(float(np.mean(results['rpm'])), 2),
            "anomaly_count": sum(1 for a in results['anomalies'] if a == -1),
            "bitstream": results['bitstream'],
            "rpm_values": results['rpm'],
            "anomalies": results['anomalies'].tolist()
        })
    
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

@app.route("/compare", methods=["POST"])
def compare():
    """Compare two videos"""
    if "video1" not in request.files or "video2" not in request.files:
        return jsonify({"error": "Please upload two videos"})
    
    video1 = request.files["video1"]
    video2 = request.files["video2"]
    
    if video1.filename == "" or video2.filename == "":
        return jsonify({"error": "Please select two videos"})
    
    video1_id = str(uuid.uuid4())
    video2_id = str(uuid.uuid4())
    video1_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video1_id}.mp4")
    video2_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video2_id}.mp4")
    
    video1.save(video1_path)
    video2.save(video2_path)

    try:
        # Process both videos
        results1 = process_video(video1_path)
        results2 = process_video(video2_path)
        
        if not results1['rpm'] or not results2['rpm']:
            return jsonify({"error": "Could not process one or both videos"})

        # Create comparison plot
        min_len = min(len(results1['rpm']), len(results2['rpm']))
        time_axis = list(range(min_len))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_axis, 
            y=results1['rpm'][:min_len],
            mode='lines',
            name='Video 1 RPM',
            line=dict(color='blue')
        ))
        fig.add_trace(go.Scatter(
            x=time_axis, 
            y=results2['rpm'][:min_len],
            mode='lines',
            name='Video 2 RPM',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title='Comparison of Fan RPM Patterns',
            xaxis_title='Time Window',
            yaxis_title='RPM',
            hovermode='closest'
        )
        
        plot_comparison = jsonlib.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        response = {
            "success": True,
            "video1": {
                "message": results1['message'],
                "avg_rpm": round(float(np.mean(results1['rpm'])), 2),
                "anomaly_count": sum(1 for a in results1['anomalies'] if a == -1)
            },
            "video2": {
                "message": results2['message'],
                "avg_rpm": round(float(np.mean(results2['rpm'])), 2),
                "anomaly_count": sum(1 for a in results2['anomalies'] if a == -1)
            },
            "plot_comparison": plot_comparison
        }
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"})

@app.route("/download/<video_id>")
def download(video_id):
    # Check if this analysis exists in session
    if 'last_analysis' not in session or session['last_analysis']['video_id'] != video_id:
        return jsonify({"error": "Analysis not found"}), 404
    
    results = session['last_analysis']['results']
    
    # Generate static plots for PDF
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Brightness over time
    axes[0, 0].plot(results['brightness'], color='blue')
    axes[0, 0].set_title("Brightness Over Time")
    axes[0, 0].set_xlabel("Frame")
    axes[0, 0].set_ylabel("Brightness")
    axes[0, 0].grid(True, alpha=0.3)
    
    # RPM over time
    axes[0, 1].plot(results['rpm'], color='green')
    axes[0, 1].set_title("RPM Over Time")
    axes[0, 1].set_xlabel("Time Window")
    axes[0, 1].set_ylabel("RPM")
    axes[0, 1].grid(True, alpha=0.3)
    
    # FFT Spectrum
    brightness_array = np.array(results['brightness'])
    fft_res = np.fft.fft(brightness_array - np.mean(brightness_array))
    freqs_full = np.fft.fftfreq(len(brightness_array), d=1/results['fps'])
    mag_full = np.abs(fft_res)
    axes[1, 0].plot(freqs_full[:len(freqs_full)//2], mag_full[:len(mag_full)//2], color='red')
    axes[1, 0].set_title("FFT Spectrum")
    axes[1, 0].set_xlabel("Frequency (Hz)")
    axes[1, 0].set_ylabel("Magnitude")
    axes[1, 0].grid(True, alpha=0.3)
    
    # Anomaly detection
    anomalies = [i for i, a in enumerate(results['anomalies']) if a == -1]
    normal_rpm = [rpm for i, rpm in enumerate(results['rpm']) if i not in anomalies]
    anomaly_rpm = [results['rpm'][i] for i in anomalies]
    axes[1, 1].plot(range(len(normal_rpm)), normal_rpm, 'go', label='Normal')
    axes[1, 1].plot(anomalies, anomaly_rpm, 'rx', label='Anomaly')
    axes[1, 1].set_title("Anomaly Detection")
    axes[1, 1].set_xlabel("Time Window")
    axes[1, 1].set_ylabel("RPM")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{video_id}_plots.png")
    plt.savefig(plot_path)
    plt.close()
    
    # Generate PDF report
    report_path = generate_pdf_report(results, video_id, [plot_path])
    
    return send_file(report_path, as_attachment=True, download_name="fan_analysis_report.pdf")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')