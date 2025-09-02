document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const videoFile = document.getElementById('videoFile');
    const resultsSection = document.getElementById('resultsSection');
    const errorMessage = document.getElementById('errorMessage');
    const loading = document.getElementById('loading');
    const messageBox = document.getElementById('messageBox');
    const avgRpm = document.getElementById('avgRpm');
    const bitstream = document.getElementById('bitstream');
    const analysisGraph = document.getElementById('analysisGraph');
    const downloadReport = document.getElementById('downloadReport');
    const analyzeAnother = document.getElementById('analyzeAnother');
    
    let currentVideoId = null;
    
    // Drag and drop functionality
    uploadBox.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#2980b9';
        this.style.backgroundColor = 'rgba(52, 152, 219, 0.2)';
    });
    
    uploadBox.addEventListener('dragleave', function() {
        this.style.borderColor = '#3498db';
        this.style.backgroundColor = 'rgba(52, 152, 219, 0.05)';
    });
    
    uploadBox.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '#3498db';
        this.style.backgroundColor = 'rgba(52, 152, 219, 0.05)';
        
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    videoFile.addEventListener('change', function() {
        if (this.files.length) {
            handleFile(this.files[0]);
        }
    });
    
    function handleFile(file) {
        // Validate file type
        if (!file.type.startsWith('video/')) {
            showError('Please upload a video file');
            return;
        }
        
        // Show loading state
        loading.style.display = 'block';
        errorMessage.style.display = 'none';
        
        // Create FormData and send via AJAX
        const formData = new FormData();
        formData.append('video', file);
        
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Display results
            currentVideoId = data.video_id;
            messageBox.textContent = data.secret_message;
            avgRpm.textContent = data.avg_rpm;
            bitstream.textContent = data.bitstream;
            analysisGraph.src = data.graph_url;
            
            resultsSection.style.display = 'block';
            
            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        })
        .catch(error => {
            loading.style.display = 'none';
            showError('An error occurred during processing: ' + error.message);
        });
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        
        // Hide error after 5 seconds
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
    
    // Download report handler
    downloadReport.addEventListener('click', function() {
        if (!currentVideoId) return;
        
        const message = encodeURIComponent(messageBox.textContent);
        const rpm = encodeURIComponent(avgRpm.textContent);
        const bits = encodeURIComponent(bitstream.textContent);
        
        window.location.href = `/download/${currentVideoId}?message=${message}&rpm=${rpm}&bits=${bits}`;
    });
    
    // Analyze another handler
    analyzeAnother.addEventListener('click', function() {
        resultsSection.style.display = 'none';
        videoFile.value = '';
        currentVideoId = null;
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});