document.addEventListener('DOMContentLoaded', () => {
    // ==========================================
    // 1. Tab Navigation Logic
    // ==========================================
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.getAttribute('data-tab')).classList.add('active');
        });
    });

    // ==========================================
    // 2. Sliders Update Logic
    // ==========================================
    const updateVal = (id) => {
        document.getElementById(id).addEventListener('input', (e) => {
            document.getElementById(`${id}-val`).textContent = e.target.value;
            if(id === 'noise') {
                const types = ["Wiener", "Wavelet", "Gaussian"];
                document.getElementById('noise-val').textContent = types[e.target.value - 1];
            }
        });
    };
    updateVal('quality'); 
    updateVal('scale'); 
    updateVal('noise');

    // ==========================================
    // 3. Image Upload Handling
    // ==========================================
    const imageUpload = document.getElementById('imageUpload');
    const uploadText = document.getElementById('upload-text');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    // Select all image elements that need the uploaded source
    const previewImages = document.querySelectorAll('.preview-img');
    const baseImg = document.querySelector('.base-img');

    imageUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            uploadText.textContent = file.name;
            const reader = new FileReader();
            reader.onload = function(event) {
                const imgUrl = event.target.result;
                
                // Populate all classical signal grids
                previewImages.forEach(img => {
                    img.src = imgUrl;
                    img.style.display = 'block';
                    img.style.opacity = '1';
                    img.classList.remove('ela-applied'); // Reset mock filters
                });
                
                // Populate fusion tab
                baseImg.src = imgUrl;
                baseImg.style.display = 'block';
                document.querySelector('.heatmap-overlay').style.display = 'none';
                
                analyzeBtn.disabled = false;
            }
            reader.readAsDataURL(file);
        }
    });

    // ==========================================
    // 4. REAL Analysis Execution via FastAPI
    // ==========================================
    analyzeBtn.addEventListener('click', async () => {
        const file = imageUpload.files[0];
        if (!file) {
            alert("Please upload an image first.");
            return;
        }

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Processing ELA in Python Backend...";
        
        const progContainer = document.getElementById('progress-container');
        const progText = document.getElementById('progress-text');
        
        progContainer.style.display = 'block';
        progText.textContent = "> Sending image to Python FastAPI Engine...";
        document.getElementById('progress-bar').style.width = "40%";
        
        // Hide images during processing to show activity
        previewImages.forEach(img => img.style.opacity = '0.3');

        // Package the image to send to Python
        const formData = new FormData();
        formData.append("file", file);

        try {
            // Send request to your FastAPI server running on localhost:8000
            const response = await fetch("http://localhost:8000/api/analyze/ela", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                progText.textContent = "> Math complete. Rendering real ELA heatmap...";
                document.getElementById('progress-bar').style.width = "100%";
                
                // Get the real generated image back from Python
                const blob = await response.blob();
                const realElaUrl = URL.createObjectURL(blob);
                
                setTimeout(() => {
                    progContainer.style.display = 'none';
                    analyzeBtn.textContent = "Analysis Complete";
                    
                    // Show all images again
                    previewImages.forEach(img => img.style.opacity = '1');
                    
                    // UPDATE CARD 1 WITH THE REAL AI DATA
                    previewImages[0].src = realElaUrl;
                    previewImages[0].classList.remove('ela-applied'); // Remove CSS fake filter
                    
                    // Keep CSS fake filters for the remaining 3 unbuilt signals
                    for(let i = 1; i < 4; i++) {
                        previewImages[i].classList.add('ela-applied');
                    }
                    
                    // Reveal Neural Fusion overlay on Tab 2
                    document.querySelector('.heatmap-overlay').style.display = 'block';
                    
                    setTimeout(() => {
                        analyzeBtn.disabled = false;
                        analyzeBtn.textContent = "Run Full Analysis";
                    }, 2000);
                }, 1000);
            } else {
                throw new Error("Backend failed to process image.");
            }
        } catch (error) {
            alert("Connection Error: Make sure your Python FastAPI server is running! (Run 'python main.py' in terminal)");
            console.error(error);
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = "Run Full Analysis";
            progContainer.style.display = 'none';
        }
    });
});