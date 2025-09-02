document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.getElementById('uploadBox');
    const uploadBox1 = document.getElementById('uploadBox1');
    const uploadBox2 = document.getElementById('uploadBox2');
    const videoFile = document.getElementById('videoFile');
    const videoFile1 = document.getElementById('videoFile1');
    const videoFile2 = document.getElementById('videoFile2');
    const resultsSection = document.getElementById('resultsSection');
    const comparisonResults = document.getElementById('comparisonResults');
    const errorMessage = document.getElementById('errorMessage');
    const loading = document.getElementById('loading');
    const messageBox = document.getElementById('messageBox');
    const avgRpm = document.getElementById('avgRpm');
    const anomalyCount = document.getElementById('anomalyCount');
    const bitstream = document.getElementById('bitstream');
    const downloadReport = document.getElementById('downloadReport');
    const analyzeAnother = document.getElementById('analyzeAnother');
    const compareBtn = document.getElementById('compareBtn');
    const compareAnother = document.getElementById('compareAnother');
    const themeToggle = document.getElementById('themeToggle');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    let currentVideoId = null;
    
    // Theme toggle functionality
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        if (document.body.classList.contains('dark-mode')) {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            themeInlineHTML = '<i class="fas fa-moon"></i>';
        }
    });
    
    // Tab switching functionality
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active tab button
            tabBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Show active tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabId}Tab`) {
                    content.classList.add('active');
                }
            });
            
            // Clear any existing results
            resultsSection.style.display = 'none';
            comparisonResults.style.display = 'none';
        });
    });
    
    // Drag and drop functionality for single upload
    setupDragDrop(uploadBox, videoFile);
    
    // Drag and drop functionality for comparison uploads
    setupDragDrop(uploadBox1, videoFile1);
    setupDragDrop(uploadBox2, videoFile2);
    
    function setupDragDrop(dropZone, fileInput) {
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.style.borderColor = '#2980b9';
            this.style.backgroundColor = 'rgba(52, 152, 219, 0.2)';
        });
        
        dropZone.addEventListener('dragleave', function() {
            this.style.borderColor = '#3498db';
            this.style.backgroundColor = '';
            if (document.body.classList.contains('dark-mode')) {
                this.style.backgroundColor = 'rgba(52, 152, 219, 0.1)';
            }
        });
        
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.style.borderColor = '#3498db';
            this.style.backgroundColor = '';
            if (document.body.classList.contains('dark-mode')) {
                this.style.backgroundColor = 'rgba(52, 152, 219, 0.1)';
            }
            
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                this.querySelector('p').textContent = `File selected: ${e.dataTransfer.files[0].name}`;
            }
        });
    }
    
    videoFile.addEventListener('change', function() {
        if (this.files.length) {
            handleFile(this.files[0], 'single');
        }
    });
    
    videoFile1.addEventListener('change', function() {
        if (this.files.length) {
            uploadBox1.querySelector('p').textContent = `File selected: ${this.files[0].name}`;
        }
    });
    
    videoFile2.addEventListener('change', function() {
        if (this.files.length) {
            uploadBox2.querySelector('p').textContent = `File selected: ${this.files[0].name}`;
        }
    });
    
    compareBtn.addEventListener('click', function() {
        if (!videoFile1.files.length || !videoFile2.files.length) {
            showError('Please select two videos to compare');
            return;
        }
        
        handleComparison(videoFile1.files[0], videoFile2.files[0]);
    });
    
    function handleFile(file, type) {
        // Validate file type
        if (!file.type.startsWith('video/')) {
            showError('Please upload a video file');
            return;
        }
        
        // Show loading state
        loading.style.display = 'block';
        errorMessage.style.display = 'none';
        resultsSection.style.display = 'none';
        comparisonResults.style.display = 'none';
        
        // Create FormData and send via AJAX
        const formData = new FormData();
        formData.append('video', file);
        
        const endpoint = type === 'single' ? '/analyze' : '/api/analyze';
        
        fetch(endpoint, {
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
            
            if (type === 'single') {
                // Display results for single analysis
                currentVideoId = data.video_id;
                messageBox.textContent = data.secret_message;
                avgRpm.textContent = data.avg_rpm;
                anomalyCount.textContent = data.anomaly_count;
                bitstream.textContent = data.bitstream;
                
                // Render interactive plots
                if (data.plot_rpm) {
                    Plotly.newPlot('rpmPlot', JSON.parse(data.plot_rpm));
                }
                if (data.plot_brightness) {
                    Plotly.newPlot('brightnessPlot', JSON.parse(data.plot_brightness));
                }
                if (data.plot_fft) {
                    Plotly.newPlot('fftPlot', JSON.parse(data.plot_fft));
                }
                
                resultsSection.style.display = 'block';
                
                // Scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                // API response
                console.log('API Analysis Result:', data);
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            showError('An error occurred during processing: ' + error.message);
        });
    }
    
    function handleComparison(file1, file2) {
        // Validate file types
        if (!file1.type.startsWith('video/') || !file2.type.startsWith('video/')) {
            showError('Please upload video files');
            return;
        }
        
        // Show loading state
        loading.style.display = 'block';
        errorMessage.style.display = 'none';
        resultsSection.style.display = 'none';
        comparisonResults.style.display = 'none';
        
        // Create FormData and send via AJAX
        const formData = new FormData();
        formData.append('video1', file1);
        formData.append('video2', file2);
        
        fetch('/compare', {
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
            
            // Display comparison results
            document.getElementById('compareMessage1').textContent = data.video1.message;
            document.getElementById('compareRpm1').textContent = data.video1.avg_rpm;
            document.getElementById('compareAnomaly1').textContent = data.video1.anomaly_count;
            
            document.getElementById('compareMessage2').textContent = data.video2.message;
            document.getElementById('compareRpm2').textContent = data.video2.avg_rpm;
            document.getElementById('compareAnomaly2').textContent = data.video2.anomaly_count;
            
            // Render comparison plot
            if (data.plot_comparison) {
                Plotly.newPlot('comparisonPlot', JSON.parse(data.plot_comparison));
            }
            
            comparisonResults.style.display = 'block';
            
            // Scroll to results
            comparisonResults.scrollIntoView({ behavior: 'smooth' });
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
        
        window.location.href = `/download/${currentVideoId}`;
    });
    
    // Analyze another handler
    analyzeAnother.addEventListener('click', function() {
        resultsSection.style.display = 'none';
        videoFile.value = '';
        currentVideoId = null;
        uploadBox.querySelector('p').textContent = 'Drag & drop a video file here or click to browse';
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    
    // Compare another handler
    compareAnother.addEventListener('click', function() {
        comparisonResults.style.display = 'none';
        videoFile1.value = '';
        videoFile2.value = '';
        uploadBox1.querySelector('p').textContent = 'Drag & drop first video';
        uploadBox2.querySelector('p').textContent = 'Drag & drop second video';
        
        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});