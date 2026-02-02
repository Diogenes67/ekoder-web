// EKoder Frontend JavaScript

const API_URL = '/api/v1';

// Authentication
function getToken() {
    return localStorage.getItem('ekoder_token');
}

function getAuthHeaders() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/static/login.html';
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            localStorage.removeItem('ekoder_token');
            window.location.href = '/static/login.html';
            return;
        }

        const user = await response.json();
        const userBar = document.getElementById('user-bar');
        const userName = document.getElementById('user-name');
        if (userBar && userName) {
            userName.textContent = user.name || user.email;
            userBar.classList.remove('hidden');
        }
    } catch (error) {
        console.error('Auth check failed:', error);
    }
}

function logout() {
    localStorage.removeItem('ekoder_token');
    window.location.href = '/static/login.html';
}

// Check auth on page load
checkAuth();

// DOM Elements
const clinicalTextEl = document.getElementById('clinical-text');
const submitBtn = document.getElementById('submit-btn');
const uploadBtn = document.getElementById('upload-btn');
const resultSection = document.getElementById('result-section');
const errorDisplay = document.getElementById('error-display');
const codeValue = document.getElementById('code-value');
const descriptor = document.getElementById('descriptor');
const reasoning = document.getElementById('reasoning');
const confidence = document.getElementById('confidence');
const candidatesBody = document.getElementById('candidates-body');
const candidateCount = document.getElementById('candidate-count');
const fileUpload = document.getElementById('file-upload');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const dropZone = document.getElementById('drop-zone');

// Current result for copy functionality
let currentCode = null;
let selectedFile = null;

// Tab switching
function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab-btn');
    const textInput = document.getElementById('text-input');
    const fileInput = document.getElementById('file-input');

    tabs.forEach(t => t.classList.remove('active'));

    if (tab === 'text') {
        tabs[0].classList.add('active');
        textInput.classList.remove('hidden');
        fileInput.classList.add('hidden');
    } else {
        tabs[1].classList.add('active');
        textInput.classList.add('hidden');
        fileInput.classList.remove('hidden');
    }
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        selectFile(file);
    }
}

function selectFile(file) {
    const validTypes = ['.txt', '.pdf', '.docx'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!validTypes.includes(ext)) {
        showError('Invalid file type. Please upload .txt, .pdf, or .docx');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileInfo.classList.remove('hidden');
    uploadBtn.disabled = false;
}

function clearFile() {
    selectedFile = null;
    fileUpload.value = '';
    fileInfo.classList.add('hidden');
    uploadBtn.disabled = true;
}

// Drag and drop (initialize when DOM is ready)
if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) {
            selectFile(file);
        }
    });
}

// Submit file
async function submitFile() {
    if (!selectedFile) {
        showError('Please select a file first.');
        return;
    }

    setUploadLoading(true);
    hideError();
    resultSection.classList.add('hidden');

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch(`${API_URL}/code/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Upload failed');
        }

        displayResult(data);

    } catch (error) {
        console.error('Error:', error);
        showError(`Error: ${error.message}. Please try again.`);
    } finally {
        setUploadLoading(false);
    }
}

function setUploadLoading(loading) {
    uploadBtn.disabled = loading;
    uploadBtn.querySelector('.btn-text').textContent = loading ? 'Processing...' : 'Code File';
    uploadBtn.querySelector('.spinner').classList.toggle('hidden', !loading);
}

async function submitCase() {
    const clinicalText = clinicalTextEl.value.trim();

    if (!clinicalText) {
        showError('Please enter clinical notes before submitting.');
        return;
    }

    if (clinicalText.length < 10) {
        showError('Clinical notes are too short. Please provide more detail.');
        return;
    }

    // Show loading state
    setLoading(true);
    hideError();
    resultSection.classList.add('hidden');

    try {
        const response = await fetch(`${API_URL}/code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                clinical_text: clinicalText
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }

        displayResult(data);

    } catch (error) {
        console.error('Error:', error);
        showError(`Error: ${error.message}. Please try again.`);
    } finally {
        setLoading(false);
    }
}

function displayResult(data) {
    resultSection.classList.remove('hidden');
    const complexityDisplay = document.getElementById('complexity-display');
    const complexityIndicator = document.getElementById('complexity-indicator');

    // Handle errors from API
    if (data.error) {
        if (data.candidates && data.candidates.length > 0) {
            showError(data.error);
        } else {
            showError(data.error);
            return;
        }
    } else {
        hideError();
    }

    // Display suggested code
    if (data.suggested_code) {
        currentCode = data.suggested_code;
        codeValue.textContent = data.suggested_code;
        codeValue.style.color = '#059669'; // success color
        descriptor.textContent = data.descriptor || '-';
        reasoning.textContent = data.reasoning || '';

        // Display complexity
        if (complexityDisplay && complexityIndicator) {
            const level = data.complexity || 1;
            if (level >= 1 && level <= 6) {
                complexityDisplay.classList.remove('hidden');
                const label = data.complexity_label || `Level ${level}`;
                complexityIndicator.innerHTML = getComplexityBars(level) + ' ' + label;
                complexityIndicator.className = 'complexity-indicator complexity-' + level;
            }
        }
    } else {
        currentCode = null;
        codeValue.textContent = 'No code suggested';
        codeValue.style.color = '#d97706'; // warning color
        descriptor.textContent = 'Please select from candidates below';
        reasoning.textContent = '';
        if (complexityDisplay) complexityDisplay.classList.add('hidden');
    }

    // Display candidates
    candidatesBody.innerHTML = '';
    if (data.candidates && data.candidates.length > 0) {
        candidateCount.textContent = data.candidates.length;

        data.candidates.forEach(candidate => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${candidate.code}</td>
                <td>${candidate.descriptor}</td>
                <td>${(candidate.score * 100).toFixed(1)}%</td>
                <td>${candidate.source}</td>
            `;
            row.style.cursor = 'pointer';
            row.onclick = () => selectCandidate(candidate);
            candidatesBody.appendChild(row);
        });
    } else {
        candidateCount.textContent = '0';
    }

    // Display extracted text (for file uploads)
    const extractedTextSection = document.getElementById('extracted-text-section');
    const extractedTextEl = document.getElementById('extracted-text');
    if (data.extracted_text && extractedTextSection && extractedTextEl) {
        extractedTextSection.classList.remove('hidden');
        extractedTextEl.textContent = data.extracted_text;
    } else if (extractedTextSection) {
        extractedTextSection.classList.add('hidden');
    }
}

function selectCandidate(candidate) {
    currentCode = candidate.code;
    codeValue.textContent = candidate.code;
    codeValue.style.color = '#2563eb'; // primary color (manually selected)
    descriptor.textContent = candidate.descriptor;
    reasoning.textContent = '(Manually selected from candidates)';

    // Update complexity for selected candidate
    const complexityDisplay = document.getElementById('complexity-display');
    const complexityIndicator = document.getElementById('complexity-indicator');
    if (candidate.complexity && complexityDisplay && complexityIndicator) {
        complexityDisplay.classList.remove('hidden');
        const level = candidate.complexity;
        const labels = ['', 'Minor (1)', 'Low (2)', 'Moderate (3)', 'Significant (4)', 'High (5)', 'Very High (6)'];
        complexityIndicator.innerHTML = getComplexityBars(level) + ' ' + (labels[level] || `Level ${level}`);
        complexityIndicator.className = 'complexity-indicator complexity-' + level;
    }
}

function getComplexityBars(level) {
    // Ensure level is between 1 and 6
    const safeLevel = Math.max(1, Math.min(6, level || 1));
    const filled = safeLevel;
    const empty = 6 - safeLevel;
    return '<span class="complexity-bars">' +
        '<span class="bar filled"></span>'.repeat(filled) +
        '<span class="bar"></span>'.repeat(empty) +
        '</span>';
}

function copyCode() {
    if (!currentCode) return;

    navigator.clipboard.writeText(currentCode).then(() => {
        // Show feedback
        const copyBtn = document.querySelector('.copy-btn');
        const originalHTML = copyBtn.innerHTML;
        copyBtn.innerHTML = '✓';
        setTimeout(() => {
            copyBtn.innerHTML = originalHTML;
        }, 1500);
    }).catch(err => {
        console.error('Copy failed:', err);
    });
}

function setLoading(loading) {
    submitBtn.disabled = loading;
    submitBtn.querySelector('.btn-text').textContent = loading ? 'Processing...' : 'Get Code';
    submitBtn.querySelector('.spinner').classList.toggle('hidden', !loading);
}

function showError(message) {
    errorDisplay.textContent = message;
    errorDisplay.classList.remove('hidden');
}

function hideError() {
    errorDisplay.classList.add('hidden');
}

// Allow Ctrl+Enter to submit
clinicalTextEl.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        submitCase();
    }
});

// Check API health on load
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        console.log('API Health:', data);
    } catch (error) {
        console.warn('API not available:', error);
    }
}

checkHealth();
