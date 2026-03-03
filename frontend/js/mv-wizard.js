/**
 * MV Wizard Controller
 * 6단계 뮤직비디오 제작 위자드 컨트롤러
 */

const API_BASE = 'http://localhost:8000/api/story-to-mv';
const YOUTUBE_API = 'http://localhost:8000/api/youtube';

class MVWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 6;
        this.sessionId = null;
        this.sessionData = null;

        // URL 파라미터에서 세션 ID 확인
        const urlParams = new URLSearchParams(window.location.search);
        const existingSessionId = urlParams.get('session_id');
        const youtubeAuth = urlParams.get('youtube_auth');
        const youtubeError = urlParams.get('youtube_error');

        if (existingSessionId) {
            this.sessionId = existingSessionId;
            this.loadSession();
        }

        if (youtubeAuth === 'success') {
            this.showToast('YouTube 인증 완료!', 'success');
        }
        if (youtubeError) {
            this.showToast(`YouTube 인증 실패: ${youtubeError}`, 'error');
        }

        this.init();
    }

    init() {
        this.bindEvents();
        this.updateProgress();
    }

    bindEvents() {
        // 스토리 입력 카운터
        const storyTextarea = document.getElementById('storyInput');
        if (storyTextarea) {
            storyTextarea.addEventListener('input', () => {
                const counter = document.getElementById('storyCounter');
                if (counter) {
                    counter.textContent = `${storyTextarea.value.length}자`;
                }
            });
        }

        // 장르 버튼
        document.querySelectorAll('.genre-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.genre-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // 공개 설정 옵션
        document.querySelectorAll('.privacy-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                document.querySelectorAll('.privacy-option').forEach(o => o.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });
    }

    // ========== 세션 관리 ==========

    async createSession() {
        try {
            const response = await fetch(`${API_BASE}/session/create`, {
                method: 'POST'
            });
            const data = await response.json();
            this.sessionId = data.session_id;
            console.log('[Wizard] Session created:', this.sessionId);

            // URL 업데이트
            history.replaceState(null, '', `?session_id=${this.sessionId}`);

            return this.sessionId;
        } catch (error) {
            console.error('Session creation failed:', error);
            throw error;
        }
    }

    async loadSession() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}`);
            if (response.ok) {
                this.sessionData = await response.json();
                console.log('[Wizard] Session loaded:', this.sessionData);

                // 현재 단계로 이동
                this.currentStep = this.sessionData.current_step || 1;
                this.updateProgress();
                this.showStep(this.currentStep);
                this.restoreUI();
            }
        } catch (error) {
            console.error('Session load failed:', error);
        }
    }

    restoreUI() {
        if (!this.sessionData) return;

        // 스토리 복원
        if (this.sessionData.story) {
            const storyInput = document.getElementById('storyInput');
            if (storyInput) storyInput.value = this.sessionData.story;
        }

        // 분석 결과 복원
        if (this.sessionData.analysis) {
            this.displayAnalysis(this.sessionData.analysis);
        }

        // 가사 복원
        if (this.sessionData.lyrics) {
            const lyricsTextarea = document.getElementById('lyricsTextarea');
            if (lyricsTextarea) lyricsTextarea.value = this.sessionData.lyrics.lyrics;
        }

        // 음악 복원
        if (this.sessionData.music) {
            this.displayMusic(this.sessionData.music);
        }

        // 이미지 복원
        if (this.sessionData.images && this.sessionData.images.length > 0) {
            this.displayImages(this.sessionData.images);
        }

        // 비디오 클립 복원
        if (this.sessionData.video_clips && this.sessionData.video_clips.length > 0) {
            this.displayVideoClips(this.sessionData.video_clips);
        }

        // 최종 비디오 복원
        if (this.sessionData.final_video) {
            this.displayFinalVideo(this.sessionData.final_video);
        }
    }

    // ========== 네비게이션 ==========

    goToStep(step) {
        if (step < 1 || step > this.totalSteps) return;
        this.currentStep = step;
        this.updateProgress();
        this.showStep(step);
    }

    nextStep() {
        if (this.currentStep < this.totalSteps) {
            this.goToStep(this.currentStep + 1);
        }
    }

    prevStep() {
        if (this.currentStep > 1) {
            this.goToStep(this.currentStep - 1);
        }
    }

    updateProgress() {
        document.querySelectorAll('.wizard-step').forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');

            if (stepNum < this.currentStep) {
                step.classList.add('completed');
            } else if (stepNum === this.currentStep) {
                step.classList.add('active');
            }
        });
    }

    showStep(step) {
        document.querySelectorAll('.step-panel').forEach(panel => {
            panel.classList.remove('active');
        });

        const activePanel = document.getElementById(`step${step}`);
        if (activePanel) {
            activePanel.classList.add('active');
        }
    }

    // ========== Step 1: 스토리 분석 ==========

    async analyzeStory() {
        const storyInput = document.getElementById('storyInput');
        const story = storyInput.value.trim();

        if (!story) {
            this.showToast('스토리를 입력해주세요.', 'error');
            return;
        }

        if (story.length < 50) {
            this.showToast('스토리를 50자 이상 입력해주세요.', 'error');
            return;
        }

        this.showLoading('스토리 분석 중...', 'AI가 스토리의 감정과 장면을 분석하고 있습니다.');

        try {
            // 세션 없으면 생성
            if (!this.sessionId) {
                await this.createSession();
            }

            const response = await fetch(`${API_BASE}/session/${this.sessionId}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    story: story,
                    num_scenes: 5
                })
            });

            if (!response.ok) throw new Error('분석 실패');

            const result = await response.json();
            this.sessionData = { ...this.sessionData, analysis: result, story: story };

            this.displayAnalysis(result);
            this.hideLoading();
            this.nextStep();

        } catch (error) {
            this.hideLoading();
            this.showToast('스토리 분석에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    displayAnalysis(analysis) {
        const container = document.getElementById('analysisResult');
        if (!container) return;

        container.innerHTML = `
            <div class="analysis-result">
                <div class="analysis-card">
                    <h5>감정</h5>
                    <span class="emotion-badge ${analysis.emotion}">${analysis.emotion}</span>
                </div>
                <div class="analysis-card">
                    <h5>테마</h5>
                    <span class="value">${analysis.theme}</span>
                </div>
                <div class="analysis-card">
                    <h5>장면 수</h5>
                    <span class="value">${analysis.scenes?.length || 0}개</span>
                </div>
            </div>
            <div class="summary-box mt-3">
                <h5>요약</h5>
                <p>${analysis.summary}</p>
            </div>
        `;
    }

    // ========== Step 2: 가사 생성 ==========

    async generateLyrics() {
        this.showLoading('가사 생성 중...', '스토리를 바탕으로 노래 가사를 작성하고 있습니다.');

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/lyrics`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            if (!response.ok) throw new Error('가사 생성 실패');

            const result = await response.json();
            this.sessionData.lyrics = result;

            const lyricsTextarea = document.getElementById('lyricsTextarea');
            if (lyricsTextarea) {
                lyricsTextarea.value = result.lyrics;
            }

            this.hideLoading();
            this.showToast('가사가 생성되었습니다.', 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('가사 생성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    async saveLyrics() {
        const lyricsTextarea = document.getElementById('lyricsTextarea');
        const lyrics = lyricsTextarea.value.trim();

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/lyrics`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lyrics: lyrics })
            });

            if (!response.ok) throw new Error('저장 실패');

            this.sessionData.lyrics = { lyrics: lyrics };
            this.showToast('가사가 저장되었습니다.', 'success');
            this.nextStep();

        } catch (error) {
            this.showToast('가사 저장에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    // ========== Step 3: 음악 생성 ==========

    async generateMusic() {
        const activeGenre = document.querySelector('.genre-btn.active');
        const genre = activeGenre ? activeGenre.dataset.genre : 'ballad';

        this.showLoading('음악 생성 중...', `${genre} 장르의 음악을 준비하고 있습니다.`);

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/music`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    genre: genre,
                    duration: 30.0
                })
            });

            if (!response.ok) throw new Error('음악 생성 실패');

            const result = await response.json();
            this.sessionData.music = result;

            this.displayMusic(result);
            this.hideLoading();
            this.showToast('음악이 준비되었습니다.', 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('음악 생성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    displayMusic(music) {
        const audioPlayer = document.getElementById('audioPlayer');
        if (audioPlayer) {
            audioPlayer.src = music.audio_url;
        }

        const musicInfo = document.getElementById('musicInfo');
        if (musicInfo) {
            musicInfo.innerHTML = `
                <p><strong>장르:</strong> ${music.genre}</p>
                <p><strong>길이:</strong> ${music.duration}초</p>
                ${music.sample_name ? `<p><strong>샘플:</strong> ${music.sample_name}</p>` : ''}
            `;
        }
    }

    // ========== Step 4: 이미지 생성 ==========

    async generateSceneImages() {
        this.showLoading('이미지 생성 중...', '각 장면의 이미지를 생성하고 있습니다. 잠시만 기다려주세요.');

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/images`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ style: 'cinematic' })
            });

            if (!response.ok) throw new Error('이미지 생성 실패');

            const result = await response.json();
            this.sessionData.images = result;

            this.displayImages(result);
            this.hideLoading();
            this.showToast(`${result.length}개의 이미지가 생성되었습니다.`, 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('이미지 생성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    displayImages(images) {
        const container = document.getElementById('sceneGrid');
        if (!container) return;

        container.innerHTML = images.map((img, index) => `
            <div class="scene-card" data-index="${index}">
                <div class="scene-image">
                    ${img.image_url ?
                        `<img src="${img.image_url}" alt="Scene ${index + 1}" onerror="this.parentElement.innerHTML='<div class=scene-placeholder><i class=bi-image></i><p>이미지 로드 실패</p></div>'">` :
                        `<div class="scene-placeholder"><i class="bi-image"></i><p>이미지 없음</p></div>`
                    }
                </div>
                <div class="scene-info">
                    <h5>Scene ${index + 1}</h5>
                    <p>${img.prompt?.substring(0, 50) || ''}...</p>
                    <div class="scene-actions">
                        <button class="btn-regenerate" onclick="wizard.regenerateImage(${index})">
                            <i class="bi-arrow-repeat"></i> 재생성
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async regenerateImage(index) {
        this.showLoading(`이미지 ${index + 1} 재생성 중...`);

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/images/${index}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ style: 'cinematic' })
            });

            if (!response.ok) throw new Error('재생성 실패');

            const result = await response.json();
            this.sessionData.images[index] = result;

            this.displayImages(this.sessionData.images);
            this.hideLoading();
            this.showToast(`이미지 ${index + 1}이 재생성되었습니다.`, 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('이미지 재생성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    // ========== Step 5: 비디오 클립 생성 ==========

    async generateVideoClips() {
        this.showLoading('비디오 클립 생성 중...', '이미지를 비디오로 변환하고 있습니다. 이 과정은 시간이 걸릴 수 있습니다.');

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/video-clips`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ motion_strength: 0.5 })
            });

            if (!response.ok) throw new Error('비디오 클립 생성 실패');

            const result = await response.json();
            this.sessionData.video_clips = result;

            this.displayVideoClips(result);
            this.hideLoading();
            this.showToast(`${result.length}개의 비디오 클립이 생성되었습니다.`, 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('비디오 클립 생성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    displayVideoClips(clips) {
        const container = document.getElementById('videoClipsGrid');
        if (!container) return;

        container.innerHTML = clips.map((clip, index) => `
            <div class="scene-card" data-index="${index}">
                <div class="video-preview-shorts">
                    ${clip.video_url ?
                        `<video src="${clip.video_url}" controls muted loop></video>` :
                        `<div class="scene-placeholder"><i class="bi-film"></i><p>비디오 없음</p></div>`
                    }
                </div>
                <div class="scene-info">
                    <h5>Clip ${index + 1}</h5>
                    <p>길이: ${clip.duration || 4}초</p>
                    <div class="scene-actions">
                        <button class="btn-regenerate" onclick="wizard.regenerateVideoClip(${index})">
                            <i class="bi-arrow-repeat"></i> 재생성
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async regenerateVideoClip(index) {
        this.showLoading(`비디오 클립 ${index + 1} 재생성 중...`);

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/video-clips/${index}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ motion_strength: 0.5 })
            });

            if (!response.ok) throw new Error('재생성 실패');

            const result = await response.json();
            this.sessionData.video_clips[index] = result;

            this.displayVideoClips(this.sessionData.video_clips);
            this.hideLoading();
            this.showToast(`비디오 클립 ${index + 1}이 재생성되었습니다.`, 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('비디오 클립 재생성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    // ========== Step 6: 최종 합성 ==========

    async composeFinalVideo() {
        this.showLoading('최종 비디오 합성 중...', '모든 클립과 음악을 합성하여 뮤직비디오를 완성하고 있습니다.');

        try {
            const response = await fetch(`${API_BASE}/session/${this.sessionId}/compose`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ add_subtitles: false })
            });

            if (!response.ok) throw new Error('합성 실패');

            const result = await response.json();
            this.sessionData.final_video = result;

            this.displayFinalVideo(result);
            this.hideLoading();
            this.showToast('뮤직비디오가 완성되었습니다!', 'success');

        } catch (error) {
            this.hideLoading();
            this.showToast('최종 합성에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    displayFinalVideo(video) {
        const preview = document.getElementById('finalVideoPreview');
        if (preview) {
            preview.innerHTML = `
                <video src="${video.video_url}" controls class="w-100" style="border-radius: 12px;"></video>
            `;
        }

        const info = document.getElementById('finalVideoInfo');
        if (info) {
            info.innerHTML = `
                <p><strong>해상도:</strong> ${video.resolution}</p>
                <p><strong>길이:</strong> ${video.duration}초</p>
            `;
        }
    }

    downloadVideo() {
        if (!this.sessionId) {
            this.showToast('세션을 찾을 수 없습니다.', 'error');
            return;
        }

        window.open(`${API_BASE}/session/${this.sessionId}/download`, '_blank');
    }

    // ========== YouTube ==========

    async initiateYouTubeAuth() {
        try {
            const response = await fetch(`${YOUTUBE_API}/auth?session_id=${this.sessionId}`);
            if (!response.ok) throw new Error('인증 URL 생성 실패');

            const result = await response.json();
            window.location.href = result.auth_url;

        } catch (error) {
            this.showToast('YouTube 인증에 실패했습니다.', 'error');
            console.error(error);
        }
    }

    async uploadToYouTube() {
        const title = document.getElementById('ytTitle').value.trim();
        const description = document.getElementById('ytDescription').value.trim();
        const privacy = document.querySelector('.privacy-option.active')?.dataset.privacy || 'private';

        if (!title) {
            this.showToast('제목을 입력해주세요.', 'error');
            return;
        }

        // 인증 상태 확인
        try {
            const authStatus = await fetch(`${YOUTUBE_API}/auth-status/${this.sessionId}`);
            const status = await authStatus.json();

            if (!status.is_authenticated) {
                this.showToast('먼저 YouTube 인증을 완료해주세요.', 'error');
                return;
            }
        } catch (e) {
            this.showToast('YouTube 인증을 먼저 완료해주세요.', 'error');
            return;
        }

        this.showLoading('YouTube 업로드 중...', '비디오를 YouTube에 업로드하고 있습니다.');

        try {
            const response = await fetch(`${YOUTUBE_API}/upload/${this.sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: title,
                    description: description,
                    tags: ['MusicVideo', 'AI', 'Shorts'],
                    privacy: privacy
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '업로드 실패');
            }

            const result = await response.json();
            this.hideLoading();

            // 성공 메시지 및 링크
            this.showToast('YouTube 업로드 완료!', 'success');
            window.open(result.url, '_blank');

        } catch (error) {
            this.hideLoading();
            this.showToast(`업로드 실패: ${error.message}`, 'error');
            console.error(error);
        }
    }

    // ========== UI 헬퍼 ==========

    showLoading(text = '처리 중...', subtext = '') {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.querySelector('.loading-text').textContent = text;
            overlay.querySelector('.loading-subtext').textContent = subtext;
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showToast(message, type = 'info') {
        // 기존 토스트 제거
        const existingToast = document.querySelector('.wizard-toast');
        if (existingToast) existingToast.remove();

        const toast = document.createElement('div');
        toast.className = `wizard-toast toast-${type}`;
        toast.innerHTML = `
            <i class="bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        `;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            background: ${type === 'success' ? '#2ecc71' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 10000;
            animation: slideIn 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// 전역 인스턴스
let wizard;

document.addEventListener('DOMContentLoaded', () => {
    wizard = new MVWizard();
});

// 스타일 추가
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
