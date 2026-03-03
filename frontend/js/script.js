(function () {
    'use strict';

    // Smooth scroll for anchor links
    document.querySelectorAll('a.click-scroll, a.smoothscroll').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            
            if (href.startsWith('#')) {
                e.preventDefault();
                const target = document.querySelector(href);
                
                if (target) {
                    const offsetTop = target.offsetTop - 80; // Account for sticky navbar
                    
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });

                    // Close mobile menu after clicking
                    const navbarCollapse = document.querySelector('.navbar-collapse');
                    if (navbarCollapse && navbarCollapse.classList.contains('show')) {
                        const bsCollapse = new bootstrap.Collapse(navbarCollapse);
                        bsCollapse.hide();
                    }
                }
            }
        });
    });

    // Active navigation on scroll
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section[id]');
        const scrollY = window.pageYOffset;

        sections.forEach(current => {
            const sectionHeight = current.offsetHeight;
            const sectionTop = current.offsetTop - 100;
            const sectionId = current.getAttribute('id');
            
            if (scrollY > sectionTop && scrollY <= sectionTop + sectionHeight) {
                document.querySelectorAll('.nav-link[href*=' + sectionId + ']').forEach(link => {
                    link.classList.add('active');
                });
            } else {
                document.querySelectorAll('.nav-link[href*=' + sectionId + ']').forEach(link => {
                    link.classList.remove('active');
                });
            }
        });
    });

    // Newsletter form handler
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const email = this.querySelector('input[type="email"]').value;
            
            // Here you would typically send this to your backend
            alert(`${email}로 구독 신청이 완료되었습니다! 감사합니다.`);
            this.reset();
        });
    }

    // Contact form handler
    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            // Here you would typically send this to your backend
            console.log('Form data:', data);
            alert('메시지가 성공적으로 전송되었습니다!');
            this.reset();
        });
    }

    // Story to MV form handler
    const storyToMVForm = document.getElementById('storyToMVForm');
    if (storyToMVForm) {
        storyToMVForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const buttonText = submitButton.querySelector('.button-text');
            const buttonLoader = submitButton.querySelector('.button-loader');
            const resultDiv = document.getElementById('mvResult');
            const resultContent = document.getElementById('resultContent');
            
            // Show loading state
            buttonText.classList.add('d-none');
            buttonLoader.classList.remove('d-none');
            submitButton.disabled = true;
            resultDiv.classList.add('d-none');
            
            try {
                // API 호출
                const response = await fetch('/api/story-to-mv/generate', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'API 요청 실패');
                }

                // 결과 표시
                let resultHTML = `
                    <p><strong>감정:</strong> ${data.emotion}</p>
                `;
                
                if (data.summary) {
                    resultHTML += `<p><strong>요약:</strong> ${data.summary}</p>`;
                }
                
                if (data.lyrics) {
                    resultHTML += `<p><strong>가사:</strong><br>${data.lyrics}</p>`;
                }
                
                if (data.audio_url) {
                    resultHTML += `
                        <div class="mt-3">
                            <strong>오디오:</strong><br>
                            <audio controls class="w-100 mt-2">
                                <source src="${data.audio_url}" type="audio/mpeg">
                            </audio>
                        </div>
                    `;
                }
                
                if (data.video_url) {
                    resultHTML += `
                        <div class="mt-3">
                            <strong>뮤직비디오:</strong><br>
                            <video controls class="w-100 mt-2" style="max-height: 400px;">
                                <source src="${data.video_url}" type="video/mp4">
                            </video>
                        </div>
                    `;
                }
                
                if (data.status === 'coming_soon') {
                    resultHTML += `<p class="text-muted mt-3"><small>* 현재 개발 중인 기능입니다. 실제 결과물은 추후 제공됩니다.</small></p>`;
                }
                
                resultContent.innerHTML = resultHTML;
                resultDiv.classList.remove('d-none');
                
            } catch (error) {
                console.error('Error:', error);
                resultContent.innerHTML = `
                    <div class="alert alert-danger">
                        생성 중 오류가 발생했습니다. 백엔드 서버가 실행 중인지 확인해주세요.
                        <br><small>${error.message}</small>
                    </div>
                `;
                resultDiv.classList.remove('d-none');
            } finally {
                // Reset button state
                buttonText.classList.remove('d-none');
                buttonLoader.classList.add('d-none');
                submitButton.disabled = false;
            }
        });
    }

    // Add fade-in animation on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe all playground cards and stats cards
    document.querySelectorAll('.playground-card, .stats-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // 2D to 3D form handler
    const twoDTo3DForm = document.getElementById('twoDTo3DForm');
    if (twoDTo3DForm) {
        twoDTo3DForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const buttonText = submitButton.querySelector('.button-text');
            const buttonLoader = submitButton.querySelector('.button-loader');
            const resultDiv = document.getElementById('convertResult');
            const resultContent = document.getElementById('convertResultContent');
            const previewImage = document.getElementById('preview3DImage');

            // Show loading state
            buttonText.classList.add('d-none');
            buttonLoader.classList.remove('d-none');
            submitButton.disabled = true;
            resultDiv.classList.add('d-none');

            try {
                // API 호출
                const response = await fetch('/api/2d-to-3d/convert', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'API 요청 실패');
                }

                // 결과 표시
                let resultHTML = `
                    <p><strong>상태:</strong> ${data.status}</p>
                    <p><strong>메시지:</strong> ${data.message}</p>
                    <p><strong>원본 파일:</strong> ${data.original_filename}</p>
                `;

                if (data.preview_url) {
                    resultHTML += `
                        <div class="mt-3">
                            <strong>원본 이미지:</strong><br>
                            <img src="${data.preview_url}" class="img-fluid rounded mt-2" alt="Original" style="max-width: 100%;">
                        </div>
                    `;

                    // 프리뷰 이미지 업데이트
                    if (previewImage) {
                        previewImage.src = data.preview_url;
                    }
                }

                if (data.model_url && data.status === 'success') {
                    resultHTML += `
                        <div class="mt-3">
                            <strong>3D 모델:</strong><br>
                            <div class="mt-2">
                                <a href="${data.model_url}" download class="btn btn-primary">
                                    <i class="bi-download"></i> 3D 모델 다운로드 (GLB)
                                </a>
                                <a href="https://gltf-viewer.donmccurdy.com/" target="_blank" class="btn btn-outline-secondary ms-2">
                                    온라인 뷰어로 보기
                                </a>
                            </div>
                            <small class="text-muted d-block mt-2">
                                다운로드한 GLB 파일을 온라인 뷰어에 드래그하면 3D 모델을 확인할 수 있습니다.
                            </small>
                        </div>
                    `;
                }

                resultContent.innerHTML = resultHTML;
                resultDiv.classList.remove('d-none');

            } catch (error) {
                console.error('Error:', error);
                resultContent.innerHTML = `
                    <div class="alert alert-danger">
                        변환 중 오류가 발생했습니다.
                        <br><small>${error.message}</small>
                    </div>
                `;
                resultDiv.classList.remove('d-none');
            } finally {
                // Reset button state
                buttonText.classList.remove('d-none');
                buttonLoader.classList.add('d-none');
                submitButton.disabled = false;
            }
        });
    }

    // Text to Image form handler
    const textToImageForm = document.getElementById('textToImageForm');
    if (textToImageForm) {
        textToImageForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = this.querySelector('button[type="submit"]');
            const buttonText = submitButton.querySelector('.button-text');
            const buttonLoader = submitButton.querySelector('.button-loader');
            const resultDiv = document.getElementById('imageResult');
            const resultContent = document.getElementById('imageResultContent');
            const previewImage = document.getElementById('previewImage');
            
            // Show loading state
            buttonText.classList.add('d-none');
            buttonLoader.classList.remove('d-none');
            submitButton.disabled = true;
            resultDiv.classList.add('d-none');
            
            try {
                // API 호출
                const response = await fetch('/api/text-to-image/generate', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'API 요청 실패');
                }

                // 결과 표시
                let resultHTML = `
                    <p><strong>프롬프트:</strong> ${data.prompt}</p>
                `;
                
                if (data.enhanced_prompt) {
                    resultHTML += `<p><strong>개선된 프롬프트:</strong> ${data.enhanced_prompt}</p>`;
                }
                
                resultHTML += `<p><strong>생성된 이미지:</strong> ${data.count}개</p>`;
                
                if (data.image_urls && data.image_urls.length > 0) {
                    resultHTML += `<div class="generated-images mt-3">`;
                    
                    data.image_urls.forEach((url, index) => {
                        resultHTML += `
                            <div class="mb-3">
                                <img src="${url}" class="img-fluid rounded" alt="Generated ${index + 1}" style="max-width: 100%; cursor: pointer;" onclick="document.getElementById('previewImage').src='${url}'">
                                <div class="mt-2">
                                    <a href="${url}" target="_blank" class="btn btn-sm btn-outline-primary">새 탭에서 보기</a>
                                </div>
                            </div>
                        `;
                    });
                    
                    resultHTML += `</div>`;
                    
                    // 첫 번째 이미지를 프리뷰로 표시
                    if (previewImage) {
                        previewImage.src = data.image_urls[0];
                    }
                }
                
                if (data.status === 'coming_soon') {
                    resultHTML += `<p class="text-muted mt-3"><small>* API 키 설정 후 실제 이미지가 생성됩니다.</small></p>`;
                }
                
                resultContent.innerHTML = resultHTML;
                resultDiv.classList.remove('d-none');
                
            } catch (error) {
                console.error('Error:', error);
                let errorMessage = error.message;

                // API 오류 응답에서 detail 추출 시도
                if (error.response) {
                    try {
                        const errData = await error.response.json();
                        errorMessage = errData.detail || errorMessage;
                    } catch {}
                }

                resultContent.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>이미지 생성 실패</strong>
                        <br>${errorMessage}
                    </div>
                `;
                resultDiv.classList.remove('d-none');
            } finally {
                // Reset button state
                buttonText.classList.remove('d-none');
                buttonLoader.classList.add('d-none');
                submitButton.disabled = false;
            }
        });
    }

})();
