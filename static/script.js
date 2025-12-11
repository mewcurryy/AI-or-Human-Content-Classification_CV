document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const html = document.documentElement;
    
    const currentTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    themeToggle.addEventListener('click', () => {
        const theme = html.getAttribute('data-theme');
        const newTheme = theme === 'light' ? 'dark' : 'light';
        
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
    
    function updateThemeIcon(theme) {
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-moon theme-toggle-icon';
        } else {
            themeIcon.className = 'fas fa-sun theme-toggle-icon';
        }
    }

    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.getAttribute('data-tab');
            
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadLoading = document.getElementById('uploadLoading');
    const uploadResult = document.getElementById('uploadResult');
    const uploadError = document.getElementById('uploadError');

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload();
        }
    });

    fileInput.addEventListener('change', handleFileUpload);

    function handleFileUpload() {
        if (fileInput.files.length === 0) return;
        
        const file = fileInput.files[0];
        
        uploadLoading.classList.add('show');
        uploadResult.classList.remove('show');
        uploadError.classList.remove('show');
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            uploadLoading.classList.remove('show');
            
            if (data.error) {
                uploadError.textContent = data.error;
                uploadError.classList.add('show');
            } else {
                displayResult(data, 'upload');
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('uploadImagePreview').src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        })
        .catch(error => {
            uploadLoading.classList.remove('show');
            uploadError.textContent = 'Error: ' + error.message;
            uploadError.classList.add('show');
        });
    }

    const analyzeInstagramBtn = document.getElementById('analyzeInstagramBtn');
    const instagramUrl = document.getElementById('instagramUrl');
    const instagramLoading = document.getElementById('instagramLoading');
    const instagramResult = document.getElementById('instagramResult');
    const instagramError = document.getElementById('instagramError');

    analyzeInstagramBtn.addEventListener('click', () => {
        const url = instagramUrl.value.trim();
        
        if (!url) {
            instagramError.textContent = 'Silakan masukkan URL Instagram.';
            instagramError.classList.add('show');
            return;
        }
        
        instagramLoading.classList.add('show');
        instagramResult.classList.remove('show');
        instagramError.classList.remove('show');
        
        fetch('/instagram', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            instagramLoading.classList.remove('show');
            
            if (data.error) {
                instagramError.textContent = data.error;
                instagramError.classList.add('show');
            } else {
                displayResult(data, 'instagram');
                const imgPreview = document.getElementById('instagramImagePreview');
                
                if (data.image_data) {
                    imgPreview.src = `data:image/jpeg;base64,${data.image_data}`;
                } else {
                    imgPreview.src = '';
                }
            }
        })
        .catch(error => {
            instagramLoading.classList.remove('show');
            instagramError.textContent = 'Error: ' + error.message;
            instagramError.classList.add('show');
        });
    });

    function displayResult(data, type) {
        const isHuman = data.prediction === 'Manusia';
        const confidence = data.confidence * 100;
        const probHuman = data.prob_human * 100;
        const probAI = data.prob_ai * 100;
        
        const resultIcon = document.getElementById(`${type}ResultIcon`);
        const resultTitle = document.getElementById(`${type}ResultTitle`);
        
        if (isHuman) {
            resultIcon.className = 'result-icon human';
            resultIcon.innerHTML = '<i class="fas fa-user"></i>';
            resultTitle.className = 'result-title human';
            resultTitle.textContent = 'Gambar ini sepertinya dibuat oleh Manusia';
        } else {
            resultIcon.className = 'result-icon ai';
            resultIcon.innerHTML = '<i class="fas fa-robot"></i>';
            resultTitle.className = 'result-title ai';
            resultTitle.textContent = 'Gambar ini sepertinya dibuat oleh AI';
        }
        
        document.getElementById(`${type}Confidence`).textContent = `${confidence.toFixed(2)}%`;
        
        const progressBar = document.getElementById(`${type}ProgressBar`);
        progressBar.className = `progress-fill ${isHuman ? 'human' : 'ai'}`;
        progressBar.style.width = '0%';
        
        setTimeout(() => {
            progressBar.style.width = `${confidence}%`;
        }, 100);
        
        document.getElementById(`${type}ProbHuman`).textContent = `${probHuman.toFixed(2)}%`;
        document.getElementById(`${type}ProbAI`).textContent = `${probAI.toFixed(2)}%`;
        
        document.getElementById(`${type}Result`).classList.add('show');
    }
});
