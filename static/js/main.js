// main.js - ZooBuddy 동물 이미지 분석 챗봇 (이벤트 위임 적용 버전)
document.addEventListener('DOMContentLoaded', function() {
    // ==========================================
    // 1. DOM 요소 참조 및 상태 변수
    // ==========================================
    const elements = {
        fileInput: document.getElementById('file'),
        previewArea: document.getElementById('previewArea'),
        previewImage: document.getElementById('previewImage'),
        uploadArea: document.getElementById('uploadArea'),
        messageInput: document.getElementById('messageInput'),
        sendButton: document.getElementById('sendButton'),
        loading: document.getElementById('loading'),
        dropArea: document.getElementById('dropArea'),
        messagesContainer: document.getElementById('messagesContainer')
    };
    
    // 앱 상태 관리
    const appState = {
        isAnalyzing: false,
        currentFileId: 'file', // 현재 활성화된 파일 입력 ID
        uploadCount: 0,        // 총 업로드 횟수 추적
        currentLoadingId: null // 현재 로딩 메시지 ID
    };
    
    // ==========================================
    // 2. 이벤트 리스너 등록
    // ==========================================
    
    // 초기 파일 입력 이벤트 핸들러
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // 드래그 앤 드롭 이벤트 핸들러
    setupDropArea(elements.dropArea, elements.fileInput);
    
    // 메시지 입력 이벤트 (비활성화)
    elements.messageInput.addEventListener('keydown', function(e) {
        e.preventDefault(); // 키 입력 방지
    });
    
    // 분석 버튼 이벤트
    elements.sendButton.addEventListener('click', analyzeImage);
    
    // 이벤트 위임: 메시지 컨테이너에 클릭 이벤트 리스너 추가
    elements.messagesContainer.addEventListener('click', function(event) {
        // "다른 이미지 분석하기" 버튼 클릭 감지
        if (event.target.classList.contains('action-link') && 
            event.target.textContent.includes('다른 이미지 분석하기')) {
            
            console.log('다른 이미지 분석하기 버튼 클릭 감지 (이벤트 위임)');
            startNewAnalysis();
            event.preventDefault();
        }
        
        // 파일 입력 라벨 클릭 감지 (업로드 영역)
        if (event.target.tagName === 'LABEL' && 
            event.target.classList.contains('upload-button')) {
            console.log('업로드 버튼 클릭 감지');
        }
    });
    
    // ==========================================
    // 3. 핵심 기능 구현
    // ==========================================
    
    /**
     * 파일 선택 이벤트 핸들러
     * @param {Event} event - 파일 선택 이벤트
     */
    function handleFileSelect(event) {
        const fileInput = event.target;
        
        if (fileInput.files && fileInput.files[0]) {
            processSelectedFile(fileInput.files[0], fileInput.id);
        }
    }
    
    /**
     * 선택된 파일 처리
     * @param {File} file - 선택된 파일
     * @param {string} inputId - 파일 입력 요소 ID
     */
    function processSelectedFile(file, inputId) {
        // 원본 fileInput에 파일 설정 (항상 분석에 사용)
        if (inputId !== 'file') {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            elements.fileInput.files = dataTransfer.files;
        }
        
        // 파일 읽기
        const reader = new FileReader();
        
        reader.onload = function(e) {
            // 이미지 미리보기 생성
            const previewId = getPreviewAreaId(inputId);
            createImagePreview(e.target.result, previewId);
            
            // 업로드 영역 숨기기
            const uploadAreaId = getUploadAreaId(inputId);
            hideElement(uploadAreaId);
            
            // 메시지 입력창 설정 및 보내기 버튼 활성화
            updateUIForAnalysis();
        };
        
        reader.onerror = function() {
            showErrorMessage('이미지를 읽는 중 오류가 발생했습니다.');
        };
        
        reader.readAsDataURL(file);
    }
    
    /**
     * 이미지 미리보기 생성 및 표시
     * @param {string} imageDataUrl - 이미지 데이터 URL
     * @param {string} previewId - 미리보기 영역 ID
     */
    function createImagePreview(imageDataUrl, previewId) {
        const previewRow = document.createElement('div');
        previewRow.className = 'message-row sent';
        previewRow.id = previewId;
        
        previewRow.innerHTML = `
            <div class="message-bubble image-preview">
                <img class="preview-image" src="${imageDataUrl}" alt="미리보기">
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        
        elements.messagesContainer.appendChild(previewRow);
        scrollToBottom();
    }
    
    /**
     * 이미지 분석 실행
     */
    function analyzeImage() {
        // 파일 확인
        if (!elements.fileInput.files || !elements.fileInput.files[0]) {
            showErrorMessage('이미지를 선택해 주세요.');
            return;
        }
        
        // 이미 분석 중이면 중복 방지
        if (appState.isAnalyzing) {
            return;
        }
        
        // 분석 상태 설정
        appState.isAnalyzing = true;
        
        // 로딩 표시기 생성 및 ID 저장
        appState.currentLoadingId = showLoadingIndicator();
        
        // 보내기 버튼 비활성화
        elements.sendButton.disabled = true;
        
        // FormData 생성
        const formData = new FormData();
        formData.append('file', elements.fileInput.files[0]);
        
        // API 호출
        fetch('/api/analyze/', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('이미지 분석 중 오류가 발생했습니다.');
            }
            return response.json();
        })
        .then(result => {
            // 로딩 메시지 제거
            hideLoadingIndicator(appState.currentLoadingId);
            
            // UI 상태 초기화
            resetUIAfterAnalysis();
            
            // 결과 확인
            if (!result.success || !result.animal || result.confidence < 0.4) {
                showNoRecognitionMessage();
                return;
            }
            
            // 결과 표시
            showAnimalResult(result);
        })
        .catch(error => {
            console.error('Error:', error);
            
            // 로딩 메시지 제거
            hideLoadingIndicator(appState.currentLoadingId);
            
            // UI 상태 초기화
            resetUIAfterAnalysis();
            
            // 오류 메시지 표시
            showErrorMessage(`오류가 발생했습니다: ${error.message}`);
        })
        .finally(() => {
            // 분석 상태 초기화
            appState.isAnalyzing = false;
        });
    }
    
    /**
     * 동물 분석 결과 표시 (API 호출 부분 제거)
     * @param {Object} result - 분석 결과 객체
     */
    function showAnimalResult(result) {
        // API 호출 없이 바로 결과 표시
        try {
            // 동물 이름 메시지 생성
            const animalMessage = result.animal ? 
                `${result.animal.replace('a ', '')} 사진이네요!` : 
                '동물 사진이네요!';
            
            // 메시지 표시
            addReceivedMessage(animalMessage);
            
            // 설명 정보 표시
            if (result.friendly_message) {
                const sentences = splitIntoSentences(result.friendly_message);
                const messages = createMessages(sentences);
                
                // 순차적으로 메시지 표시
                showMessagesSequentially(messages, function() {
                    // 모든 메시지 표시 후 액션 버튼 추가
                    addActionButton();
                });
            } else {
                // 정보가 없는 경우 바로 액션 버튼 추가
                setTimeout(() => {
                    addActionButton();
                }, 1000);
            }
        } catch (error) {
            console.error('Error:', error);
            showErrorMessage(`결과 처리 중 오류가 발생했습니다: ${error.message}`);
            
            // 오류가 발생해도 액션 버튼 제공
            setTimeout(() => {
                addActionButton();
            }, 1000);
        }
    }
    
    /**
     * 인식 실패 메시지 표시
     */
    function showNoRecognitionMessage() {
        addReceivedMessage("이 이미지에서 동물을 정확히 인식하지 못했습니다. 다른 이미지를 시도해보세요.");
        
        // 액션 버튼 추가
        setTimeout(() => {
            addActionButton();
        }, 1000);
    }
    
    /**
     * 액션 버튼 추가 ("다른 이미지 분석하기") - 이벤트 위임 방식으로 변경
     */
    function addActionButton() {
        const actionRow = document.createElement('div');
        actionRow.className = 'message-row received';
        actionRow.innerHTML = `
            <div class="message-bubble action-bubble">
                <span class="action-link">다른 이미지 분석하기</span>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        
        elements.messagesContainer.appendChild(actionRow);
        
        // 이벤트 리스너를 직접 추가하지 않고 이벤트 위임으로 처리
        scrollToBottom();
    }
    
    /**
     * 새 분석 시작 - 순환 구조 구현
     */
    function startNewAnalysis() {
        console.log("시작: 새 분석 시작");
        
        // 1. 이전 UI 상태 완전히 초기화
        resetUIForNewAnalysis();
        
        // 2. 업로드 카운트 증가 (고유 ID 생성용)
        appState.uploadCount++;
        
        // 3. 고유 ID 생성
        const newFileId = `file_${appState.uploadCount}`;
        const newUploadAreaId = `uploadArea_${appState.uploadCount}`;
        const newDropAreaId = `dropArea_${appState.uploadCount}`;
        
        // 4. 현재 활성화된 파일 입력 ID 업데이트
        appState.currentFileId = newFileId;
        
        // 5. 새 업로드 영역 생성 (중요: 매번 새로 생성)
        const newUploadRow = document.createElement('div');
        newUploadRow.className = 'message-row sent';
        newUploadRow.id = newUploadAreaId;
        newUploadRow.innerHTML = `
            <div class="message-bubble upload-area" id="${newDropAreaId}">
                <form id="new-upload-form_${appState.uploadCount}">
                    <input type="file" name="file" id="${newFileId}" accept="image/*" required hidden>
                    <label for="${newFileId}" class="upload-button">
                        <svg width="24" height="24" viewBox="0 0 24 24">
                            <path d="M19 7v2.99s-1.99.01-2 0V7h-3s.01-1.99 0-2h3V2h2v3h3v2h-3zm-3 4V8h-3V5H5c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-8h-3zM5 19l3-4 2 3 3-4 4 5H5z"></path>
                        </svg>
                        이미지 선택하기
                    </label>
                </form>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        
        // 6. 메시지 흐름에 새 업로드 영역 추가
        elements.messagesContainer.appendChild(newUploadRow);
        
        // 7. 새 파일 입력에 이벤트 핸들러 연결 (중요!)
        const newFileInput = document.getElementById(newFileId);
        if (newFileInput) {
            newFileInput.addEventListener('change', function(event) {
                console.log(`파일 선택됨: ${newFileId}`);
                // 파일 선택 시 원본 fileInput에 복사
                if (this.files && this.files[0]) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(this.files[0]);
                    elements.fileInput.files = dataTransfer.files;
                    
                    // 미리보기 생성 및 UI 업데이트
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        // 새 미리보기 영역 생성
                        const previewId = `previewArea_${appState.uploadCount}`;
                        createImagePreview(e.target.result, previewId);
                        
                        // 업로드 영역 숨기기
                        document.getElementById(newUploadAreaId).style.display = 'none';
                        
                        // 보내기 버튼 활성화
                        elements.messageInput.textContent = "우측의 보내기 버튼을 누르세요.";
                        elements.messageInput.classList.add('disabled-text');
                        elements.sendButton.disabled = false;
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
            console.log(`이벤트 리스너 연결됨: ${newFileId}`);
        } else {
            console.error(`File input element with ID ${newFileId} not found.`);
        }
        
        // 8. 새 드롭 영역에 드래그 앤 드롭 설정
        const newDropArea = document.getElementById(newDropAreaId);
        if (newDropArea) {
            setupDropArea(newDropArea, newFileInput);
            console.log(`드롭 영역 설정됨: ${newDropAreaId}`);
        } else {
            console.error(`Drop area element with ID ${newDropAreaId} not found.`);
        }
        
        // 9. 메시지 입력창 초기화
        elements.messageInput.textContent = '';
        elements.messageInput.classList.remove('disabled-text');
        
        // 10. 보내기 버튼 비활성화
        elements.sendButton.disabled = true;
        
        // 11. 스크롤 최하단으로 이동
        scrollToBottom();
        
        console.log(`새 분석 시작 완료: fileId=${newFileId}, uploadAreaId=${newUploadAreaId}`);
    }
    
    // 나머지 코드는 그대로 유지...
    // (로딩, 메시지, UI 상태 관리, 유틸리티 함수 등)
    
    /**
     * 로딩 표시기 생성 및 표시
     * @returns {string} 생성된 로딩 요소의 ID
     */
    function showLoadingIndicator() {
        // 기존 로딩 요소 제거 (중복 방지)
        removeLoadingIndicators();
        
        // 고유 ID 생성
        const loadingId = `loading_${Date.now()}`;
        
        // 새 로딩 메시지 요소 생성
        const loadingRow = document.createElement('div');
        loadingRow.className = 'message-row received';
        loadingRow.id = loadingId;
        loadingRow.innerHTML = `
            <div class="message-bubble loading-bubble">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        
        // 메시지 컨테이너에 로딩 요소 추가 (항상 마지막에 추가)
        elements.messagesContainer.appendChild(loadingRow);
        
        // 스크롤
        scrollToBottom();
        
        // 입력창 업데이트
        elements.messageInput.textContent = "분석 중...";
        elements.messageInput.classList.add('disabled-text');
        
        // 로딩 ID 반환 (나중에 제거할 때 사용)
        return loadingId;
    }
    
    /**
     * 모든 로딩 표시기 제거
     */
    function removeLoadingIndicators() {
        document.querySelectorAll('[id^="loading_"]').forEach(el => {
            el.remove();
        });
    }
    
    /**
     * 특정 로딩 표시기 제거
     * @param {string} loadingId - 제거할 로딩 표시기 ID
     */
    function hideLoadingIndicator(loadingId) {
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.remove();
        }
    }
    
    /**
     * 메시지 순차적으로 표시
     * @param {string[]} messages - 표시할 메시지 배열
     * @param {Function} callback - 모든 메시지 표시 후 실행할 콜백
     */
    function showMessagesSequentially(messages, callback) {
        let index = 0;
        
        function showNextMessage() {
            if (index < messages.length) {
                addReceivedMessage(messages[index]);
                index++;
                setTimeout(showNextMessage, 1000); // 1초 간격으로 메시지 표시
            } else if (callback) {
                callback();
            }
        }
        
        showNextMessage();
    }
    
    /**
     * 받은 메시지 추가
     * @param {string} message - 메시지 내용
     */
    function addReceivedMessage(message) {
        const messageRow = document.createElement('div');
        messageRow.className = 'message-row received';
        
        messageRow.innerHTML = `
            <div class="message-bubble">
                ${message}
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        
        elements.messagesContainer.appendChild(messageRow);
        scrollToBottom();
    }
    
    /**
     * 오류 메시지 표시
     * @param {string} message - 오류 메시지
     */
    function showErrorMessage(message) {
        const errorRow = document.createElement('div');
        errorRow.className = 'message-row received';
        errorRow.innerHTML = `
            <div class="message-bubble error-bubble">
                ${message}
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        `;
        
        elements.messagesContainer.appendChild(errorRow);
        scrollToBottom();
    }
    
    /**
     * 분석 후 UI 상태 초기화
     */
    function resetUIAfterAnalysis() {
        // 메시지 입력창 초기화
        elements.messageInput.textContent = '';
        elements.messageInput.classList.remove('disabled-text');
        
        // 보내기 버튼 상태 업데이트
        updateSendButtonState();
    }
    
    /**
     * 새 분석을 위한 UI 완전 초기화
     */
    function resetUIForNewAnalysis() {
        // 파일 입력 초기화
        elements.fileInput.value = '';
        
        // 로딩 메시지 제거
        removeLoadingIndicators();
        
        // 메시지 입력창 초기화
        elements.messageInput.textContent = '';
        elements.messageInput.classList.remove('disabled-text');
        
        // 보내기 버튼 비활성화
        elements.sendButton.disabled = true;
    }
    
    /**
     * 분석을 위한 UI 업데이트
     */
    function updateUIForAnalysis() {
        elements.messageInput.textContent = "우측의 보내기 버튼을 누르세요.";
        elements.messageInput.classList.add('disabled-text');
        elements.sendButton.disabled = false;
    }
    
    /**
     * 보내기 버튼 상태 업데이트
     */
    function updateSendButtonState() {
        // 파일이 선택되었고 분석 중이 아닐 때만 활성화
        elements.sendButton.disabled = !(elements.fileInput.files && 
                                        elements.fileInput.files[0] && 
                                        !appState.isAnalyzing);
    }
    
    /**
     * 드래그 앤 드롭 영역 설정
     * @param {HTMLElement} dropArea - 드롭 영역 요소
     * @param {HTMLElement} fileInput - 파일 입력 요소
     */
    function setupDropArea(dropArea, fileInput) {
        if (!dropArea) return;
        
        const events = ['dragenter', 'dragover', 'dragleave', 'drop'];
        events.forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.classList.add('highlight');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => {
                dropArea.classList.remove('highlight');
            }, false);
        });
        
        dropArea.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files && files.length) {
                processSelectedFile(files[0], fileInput.id);
            }
        }, false);
    }
    
    /**
     * 텍스트를 문장으로 분할
     * @param {string} text - 분할할 텍스트
     * @returns {string[]} 문장 배열
     */
    function splitIntoSentences(text) {
        // 마침표, 느낌표, 물음표로 끝나는 문장 단위로 분할
        const sentenceEnders = /([.!?])\s+/g;
        const sentences = text.split(sentenceEnders);
        
        // 분할된 문장 재구성 (구분자가 제거되는 문제 해결)
        const result = [];
        for (let i = 0; i < sentences.length - 1; i += 2) {
            if (sentences[i]) {
                result.push(sentences[i] + sentences[i+1]);
            }
        }
        
        // 마지막 부분이 구두점으로 끝나지 않는 경우 처리
        if (sentences.length % 2 === 1 && sentences[sentences.length - 1]) {
            result.push(sentences[sentences.length - 1]);
        }
        
        return result;
    }
    
    /**
     * 문장들을 메시지로 그룹화
     * @param {string[]} sentences - 문장 배열
     * @returns {string[]} 메시지 배열
     */
    function createMessages(sentences) {
        const messages = [];
        let currentMessage = "";
        const MAX_LENGTH = 150; // 메시지 최대 길이
        
        sentences.forEach(sentence => {
            // 현재 메시지에 새 문장을 추가했을 때 너무 길어지면 새 메시지 시작
            if (currentMessage.length + sentence.length > MAX_LENGTH) {
                if (currentMessage) {
                    messages.push(currentMessage.trim());
                }
                currentMessage = sentence;
            } 
            // 현재 메시지에 문장 추가
            else {
                currentMessage += (currentMessage ? " " : "") + sentence;
            }
        });
        
        // 마지막 메시지 추가
        if (currentMessage) {
            messages.push(currentMessage.trim());
        }
        
        return messages;
    }
    
    /**
     * 현재 시간 표시 형식 반환
     * @returns {string} 형식화된 시간 문자열
     */
    function getCurrentTime() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const ampm = hours >= 12 ? '오후' : '오전';
        const formattedHours = hours % 12 || 12;
        const formattedMinutes = minutes < 10 ? '0' + minutes : minutes;
        
        return `${ampm} ${formattedHours}:${formattedMinutes}`;
    }
    
    /**
     * 스크롤을 최하단으로 이동
     */
    function scrollToBottom() {
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }
    
    /**
     * 업로드 영역 ID 생성
     * @param {string} fileId - 파일 입력 요소 ID
     * @returns {string} 업로드 영역 ID
     */
    function getUploadAreaId(fileId) {
        return fileId === 'file' ? 'uploadArea' : `uploadArea_${fileId.split('_')[1]}`;
    }
    
    /**
     * 미리보기 영역 ID 생성
     * @param {string} fileId - 파일 입력 요소 ID
     * @returns {string} 미리보기 영역 ID
     */
    function getPreviewAreaId(fileId) {
        return fileId === 'file' ? 'previewArea' : `previewArea_${fileId.split('_')[1]}`;
    }
    
    /**
     * 요소 숨기기
     * @param {string} elementId - 숨길 요소 ID
     */
    function hideElement(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    }
    
    /**
     * 기본 이벤트 방지
     * @param {Event} e - 이벤트 객체
     */
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // ==========================================
    // 7. 초기화 작업
    // ==========================================
    
    // 시간 업데이트
    function updateTime() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        
        const formattedHours = hours % 12 || 12;
        const formattedMinutes = minutes < 10 ? '0' + minutes : minutes;
        
        document.querySelector('.time').textContent = `${formattedHours}:${formattedMinutes}`;
    }
    
    // 페이지 로드 시 시간 업데이트
    updateTime();
    
    // 1분마다 시간 업데이트
    setInterval(updateTime, 60000);
    
    // 초기 스크롤 위치 설정
    scrollToBottom();
});
