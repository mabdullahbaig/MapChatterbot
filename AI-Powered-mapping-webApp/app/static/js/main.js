document.addEventListener('DOMContentLoaded', () => {
    initFileUpload();
    initChatInterface();
});

// File Upload Handling (simplified)
async function initFileUpload() {
    const fileInput = document.getElementById('fileUpload');
    
    fileInput.addEventListener('change', async () => {
        const file = fileInput.files[0];
        if (!file) return;

        showToast(`Uploading ${file.name}...`, 'info');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload-file', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }

            showToast(data.message, 'success');
            
            if (data.file_type === 'raster') {
                showBandSelection(data.filepath, data.band_count || 4);
            } else {
                sessionStorage.setItem('current_file', data.filepath);
                sessionStorage.setItem('columns', JSON.stringify(data.columns));
            }
        } catch (error) {
            showToast(error.message, 'error');
            console.error('Upload error:', error);
        }
        
        fileInput.value = '';
    });
}

function showBandSelection(rasterPath, bandCount) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Select Bands for Analysis</h3>
            <div class="band-selection">
                <div class="band-option">
                    <label>NDVI (Normalized Difference Vegetation Index)</label>
                    <div class="band-inputs">
                        <input type="number" placeholder="NIR Band" class="nir-band" min="1" max="${bandCount}">
                        <input type="number" placeholder="Red Band" class="red-band" min="1" max="${bandCount}">
                        <button class="calculate-btn" data-index="NDVI">Calculate</button>
                    </div>
                </div>
                <div class="band-option">
                    <label>NDWI (Normalized Difference Water Index)</label>
                    <div class="band-inputs">
                        <input type="number" placeholder="Green Band" class="green-band" min="1" max="${bandCount}">
                        <input type="number" placeholder="NIR Band" class="nir-band" min="1" max="${bandCount}">
                        <button class="calculate-btn" data-index="NDWI">Calculate</button>
                    </div>
                </div>
                <div class="band-option">
                    <label>SAWI (Soil Adjusted Water Index)</label>
                    <div class="band-inputs">
                        <input type="number" placeholder="NIR Band" class="nir-band" min="1" max="${bandCount}">
                        <input type="number" placeholder="SWIR Band" class="swir-band" min="1" max="${bandCount}">
                        <button class="calculate-btn" data-index="SAWI">Calculate</button>
                    </div>
                </div>
            </div>
            <button class="close-modal">Close</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.querySelectorAll('.calculate-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const indexType = btn.dataset.index;
            let bands = [];
            
            if (indexType === 'NDVI') {
                bands = [
                    parseInt(modal.querySelector('.nir-band').value),
                    parseInt(modal.querySelector('.red-band').value)
                ];
            } else if (indexType === 'NDWI') {
                bands = [
                    parseInt(modal.querySelector('.green-band').value),
                    parseInt(modal.querySelector('.nir-band').value)
                ];
            } else if (indexType === 'SAWI') {
                bands = [
                    parseInt(modal.querySelector('.nir-band').value),
                    parseInt(modal.querySelector('.swir-band').value)
                ];
            }
            
            if (bands.some(isNaN)) {
                showToast('Please enter valid band numbers', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/calculate-index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        raster_path: rasterPath,
                        index_type: indexType,
                        bands: bands
                    })
                });
                
                const data = await response.json();
                if (response.ok) {
                    addAnalysisResult(indexType, data.image_data);
                } else {
                    showToast(data.error, 'error');
                }
            } catch (error) {
                showToast('Calculation failed: ' + error.message, 'error');
            }
        });
    });
    
    modal.querySelector('.close-modal').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
}

function initChatInterface() {
    const sendBtn = document.getElementById('sendBtn');
    const userInput = document.getElementById('userInput');

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
}

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';
    
    try {
        const response = await fetch('/api/process-query', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: message }) // Fixed: was sending userInput instead of message
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Request failed');
        }

        const data = await response.json();
        displayAIResponse(data);
        
    } catch (error) {
        addMessage('Error: ' + error.message, 'error');
    }
}

// Add this if using CSRF protection
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}
function addMessage(text, type) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
    chatHistory.appendChild(messageDiv);
    scrollToBottom();
}

function displayAIResponse(data) {
    const chatHistory = document.getElementById('chatHistory');
    const responseDiv = document.createElement('div');
    responseDiv.className = 'message ai';
    
    if (data.ai_response) {
        const textDiv = document.createElement('div');
        textDiv.className = 'message-content';
        textDiv.textContent = data.ai_response;
        responseDiv.appendChild(textDiv);
    }
    
    if (data.map_html) {
        const mapContainer = document.createElement('div');
        mapContainer.className = 'map-container';
        mapContainer.innerHTML = data.map_html;
        
        const scripts = mapContainer.getElementsByTagName('script');
        for (let script of scripts) {
            const newScript = document.createElement('script');
            newScript.text = script.innerHTML;
            document.body.appendChild(newScript).parentNode.removeChild(newScript);
        }
        
        responseDiv.appendChild(mapContainer);
    } else if (data.map_image) {
        const img = document.createElement('img');
        img.src = data.map_image;
        img.className = 'map-image';
        responseDiv.appendChild(img);
    }
    
    if (data.statistics) {
        const statsContainer = document.createElement('div');
        statsContainer.className = 'stats-container';
        
        if (typeof data.statistics === 'string') {
            statsContainer.innerHTML = `<p>${data.statistics}</p>`;
        } else {
            statsContainer.innerHTML = `
                <div class="stats-header">
                    <h4>Statistics</h4>
                </div>
                <div class="stats-content"></div>
            `;
            
            const statsContent = statsContainer.querySelector('.stats-content');
            for (const [col, stats] of Object.entries(data.statistics)) {
                if (typeof stats === 'string') {
                    statsContent.innerHTML += `<p>${stats}</p>`;
                } else {
                    statsContent.innerHTML += `
                        <div class="stat-item">
                            <h5>${col}</h5>
                            <ul>
                                <li>Count: ${stats['count']}</li>
                                <li>Mean: ${stats['mean']?.toFixed(2) || 'N/A'}</li>
                                <li>Std: ${stats['std']?.toFixed(2) || 'N/A'}</li>
                                <li>Min: ${stats['min']}</li>
                                <li>Max: ${stats['max']}</li>
                            </ul>
                        </div>
                    `;
                }
            }
        }
        
        responseDiv.appendChild(statsContainer);
    }
    
    chatHistory.appendChild(responseDiv);
    scrollToBottom();
}

function addAnalysisResult(indexType, imageData) {
    const chatHistory = document.getElementById('chatHistory');
    const responseDiv = document.createElement('div');
    responseDiv.className = 'message ai';
    
    responseDiv.innerHTML = `
        <div class="message-content">
            ${indexType} calculation completed
        </div>
        <img src="${imageData}" class="index-image">
    `;
    
    chatHistory.appendChild(responseDiv);
    scrollToBottom();
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function scrollToBottom() {
    const chatHistory = document.getElementById('chatHistory');
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function updateColorScheme(columnName, selectElement) {
    try {
        const scheme = selectElement.value;
        const map = window.myMap; // Access the map from the window
        if (!map) {
            console.error("Map object is not available in updateColorScheme");
            return;
        }
        Object.values(map._layers).forEach(layer => {
            if (layer.name === 'Choropleth') {
                layer.setStyle({ fillColor: scheme });
                layer.options.fillColor = scheme;
                layer.redraw();
            }
        });
    } catch (error) {
        console.error("Error in updateColorScheme:", error);
    }
}

function updateOpacity(layerName, value, inputElement) {
    try {
        const map = window.myMap; // Access the map from the window
        if (!map) {
            console.error("Map object is not available in updateOpacity");
            return;
        }
        Object.values(map._layers).forEach(layer => {
            if (layer.name === layerName) {
                layer.setStyle({ fillOpacity: parseFloat(value) });
            }
        });
    } catch (error) {
        console.error("Error in updateOpacity:", error);
    }
}
