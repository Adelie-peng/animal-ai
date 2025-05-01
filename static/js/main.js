// main.js
document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 참조
    const fileInput = document.getElementById('file');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loading = document.getElementById('loading');
    const dropArea = document.getElementById('dropArea');
    const uploadForm = document.getElementById('upload-form');

    // 파일 선택 시 미리보기
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewArea.style.display = 'block';
            }
            
            reader.readAsDataURL(this.files[0]);
        }
    });

    // 드래그 앤 드롭 기능
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files && files.length) {
            fileInput.files = files;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewArea.style.display = 'block';
            }
            reader.readAsDataURL(files[0]);
        }
    }

    // 분석 버튼 클릭 이벤트
    analyzeBtn.addEventListener('click', async function() {
        if (!fileInput.files || !fileInput.files[0]) {
            alert('이미지를 선택해 주세요.');
            return;
        }

        // 로딩 표시
        loading.style.display = 'block';
        uploadForm.style.display = 'none';
        
        // FormData 생성
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        try {
            // 백엔드 API 호출
            const response = await fetch('http://127.0.0.1:8000/api/analyze/', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('이미지 분석 중 오류가 발생했습니다.');
            }
            
            const result = await response.json();
            
            // 결과 페이지로 이동
            window.location.href = `http://127.0.0.1:8000/result?animal=${encodeURIComponent(result.animal)}&info=${encodeURIComponent(result.friendly_message)}`;
            
        } catch (error) {
            console.error('Error:', error);
            alert(error.message);
            loading.style.display = 'none';
            uploadForm.style.display = 'block';
        }
    });
});
