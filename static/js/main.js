// main.js
document.addEventListener('DOMContentLoaded', function() {
    // DOM 요소 참조
    const fileInput = document.getElementById('file');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const uploadArea = document.getElementById('uploadArea');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const loading = document.getElementById('loading');
    const dropArea = document.getElementById('dropArea');
    const messagesContainer = document.getElementById('messagesContainer');
    
    // 파일 선택 시 미리보기
    fileInput.addEventListener('change', function() {
        console.log("File selected:", this.files);
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                console.log("File loaded");
                previewImage.src = e.target.result;
                
                // 중요: 이미지 선택하기 영역을 숨기고 미리보기 표시
                uploadArea.style.display = 'none';
                previewArea.style.display = 'flex';
                
                // 입력창에 안내 메시지 표시 및 보내기 버튼 활성화
                messageInput.textContent = "우측의 보내기 버튼을 누르세요.";
                messageInput.classList.add('disabled-text');
                sendButton.disabled = false;
                
                // 스크롤을 최하단으로 이동
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
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
        console.log("File dropped");
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files && files.length) {
            fileInput.files = files;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                console.log("Dropped file loaded");
                previewImage.src = e.target.result;
                
                // 중요: 이미지 선택하기 영역을 숨기고 미리보기 표시
                uploadArea.style.display = 'none';
                previewArea.style.display = 'flex';
                
                // 입력창에 안내 메시지 표시 및 보내기 버튼 활성화
                messageInput.textContent = "우측의 보내기 버튼을 누르세요.";
                messageInput.classList.add('disabled-text');
                sendButton.disabled = false;
                
                // 스크롤을 최하단으로 이동
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
            reader.readAsDataURL(files[0]);
        }
    }

    // 보내기(분석) 버튼 클릭 이벤트
    sendButton.addEventListener('click', analyzeImage);
    
    // 엔터 키 입력 처리 (비활성화)
    messageInput.addEventListener('keydown', function(e) {
        e.preventDefault(); // 키 입력 방지
    });

    // 이미지 분석 함수
    async function analyzeImage() {
        console.log("Analyze button clicked");
        if (!fileInput.files || !fileInput.files[0]) {
            alert('이미지를 선택해 주세요.');
            return;
        }

        // 로딩 표시
        loading.style.display = 'flex';
        sendButton.disabled = true;
        messageInput.textContent = "분석 중...";
        
        // 스크롤을 최하단으로 이동
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // FormData 생성
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        try {
            // 백엔드 API 호출 - 세션에 데이터 저장
            const response = await fetch('http://127.0.0.1:8000/api/analyze/', {
                method: 'POST',
                body: formData,
                credentials: 'include'  // 쿠키/세션 포함
            });
            
            if (!response.ok) {
                throw new Error('이미지 분석 중 오류가 발생했습니다.');
            }
            
            // 결과 페이지로 이동 (쿼리 매개변수 없음)
            window.location.href = 'http://127.0.0.1:8000/result';
            
        } catch (error) {
            console.error('Error:', error);
            
            // 에러 메시지 표시
            loading.style.display = 'none';
            
            const errorRow = document.createElement('div');
            errorRow.className = 'message-row received';
            errorRow.innerHTML = `
                <div class="message-bubble">
                    오류가 발생했습니다: ${error.message}
                </div>
                <div class="message-time">방금 전</div>
            `;
            messagesContainer.appendChild(errorRow);
            
            // 메시지 입력창 및 버튼 상태 복원
            messageInput.textContent = "우측의 보내기 버튼을 누르세요.";
            sendButton.disabled = false;
            
            // 스크롤을 최하단으로 이동
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    // 시간 업데이트 (iOS 스타일)
    function updateTime() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const ampm = hours >= 12 ? '오후' : '오전';
        const formattedHours = hours % 12 || 12;
        const formattedMinutes = minutes < 10 ? '0' + minutes : minutes;
        
        const timeString = `${ampm} ${formattedHours}:${formattedMinutes}`;
        document.querySelector('.time').textContent = `${formattedHours}:${formattedMinutes}`;
        
        // 모든 "방금 전" 메시지 시간 업데이트
        const recentTimes = document.querySelectorAll('.message-time');
        recentTimes.forEach(timeEl => {
            if (timeEl.textContent === '방금 전') {
                timeEl.textContent = timeString;
            }
        });
    }
    
    // 페이지 로드 시 시간 업데이트
    updateTime();
    
    // 채팅 컨테이너를 최하단으로 스크롤
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
});
