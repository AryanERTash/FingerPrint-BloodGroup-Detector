const scanner = document.getElementById('scanner');
const fileInput = document.getElementById('file-input');
const placeholder = document.getElementById('placeholder');
const preview = document.getElementById('preview');
const scanLine = document.getElementById('scan-line');
const fileNameEl = document.getElementById('file-name');
const fileDimsEl = document.getElementById('file-dims');
const analyzeBtn = document.getElementById('analyze-btn');
const errorBox = document.getElementById('error-box');

const progressWrap = document.getElementById('progress-wrap');
const progressFill = document.getElementById('progress-fill');
const progressStatus = document.getElementById('progress-status');
const progressPct = document.getElementById('progress-pct');

const resultsEmpty = document.getElementById('results-empty');
const resultHeader = document.getElementById('result-header');
const resultCall = document.getElementById('result-call');
const resultConf = document.getElementById('result-conf');
const typeGrid = document.getElementById('type-grid');

const MAX_DIM = 256;
let selectedFile = null;

function showError(msg) {
	// for now, just show the error box and add a red border to the scanner
	errorBox.textContent = msg;
	errorBox.style.display = 'block';
	scanner.classList.add('has-error');
}
function clearError() {

	// clear the rror box
	errorBox.style.display = 'none';
	errorBox.textContent = '';
	scanner.classList.remove('has-error');
}

function resetResults() {


	resultsEmpty.style.display = 'flex';

	resultHeader.style.display = 'none';


	typeGrid.style.display = 'none';
	typeGrid.innerHTML = '';
}

scanner.addEventListener('click', () => fileInput.click());



// drag drop functionality(may not work in linux distributions)
['dragenter', 'dragover'].forEach(evt => {
	scanner.addEventListener(evt, e => {
		e.preventDefault();
		scanner.classList.add('drag-over');
	});
});


['dragleave', 'drop'].forEach(evt => {
	scanner.addEventListener(evt, e => {
		e.preventDefault();
		scanner.classList.remove('drag-over');
	});
});



scanner.addEventListener('drop', e => {
	const dropped = e.dataTransfer.files[0];
	if (dropped) handleFile(dropped);
});

fileInput.addEventListener('change', e => {
	const f = e.target.files[0];
	if (f) handleFile(f);
});



function handleFile(file) {
	clearError();
	resetResults();

	if (!['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/x-ms-bmp'].includes(file.type)) {
		showError('Unsupported file type. Upload a PNG, JPG, or BMP image.');
		analyzeBtn.disabled = true;
		return;
	}

	const img = new Image();
	const objectUrl = URL.createObjectURL(file);
	img.onload = () => {
		if (img.width > MAX_DIM || img.height > MAX_DIM) {
			showError(`Image is ${img.width}x${img.height}px. Maximum accepted size is ${MAX_DIM}x${MAX_DIM}px.`);
			analyzeBtn.disabled = true;
			URL.revokeObjectURL(objectUrl);
			return;
		}


		selectedFile = file;
		preview.src = objectUrl;
		preview.style.display = 'block';
		
		placeholder.style.display = 'none';
		scanner.classList.add('has-image');

		fileNameEl.textContent = file.name;
		fileDimsEl.textContent = `${img.width}\u00d7${img.height}px`;

		analyzeBtn.disabled = false;
	};

	img.onerror = () => {
		showError('Could not read this file as an image.');
		analyzeBtn.disabled = true;
	};
	img.src = objectUrl;
}

analyzeBtn.addEventListener('click', () => {
	if (!selectedFile) return;
	clearError();
	resetResults();
	runAnalysis(selectedFile);
});

function runAnalysis(file) {
	// analysis animation and api calls



	analyzeBtn.disabled = true;
	analyzeBtn.textContent = 'Analyzing\u2026';
	
	progressWrap.style.display = 'block';
	progressFill.style.width = '0%';
	progressPct.textContent = '0%';
	
	progressStatus.textContent = 'Uploading\u2026';
	scanLine.style.display = 'block';

	const formData = new FormData();
	formData.append('file', file);


	// api call can also use fetch api
	const xhr = new XMLHttpRequest();
	xhr.open('POST', '/api', true);

	xhr.upload.onprogress = (e) => {
		if (e.lengthComputable) {
			const pct = Math.round((e.loaded / e.total) * 100);
			progressFill.style.width = pct + '%';
			progressPct.textContent = pct + '%';
			if (pct >= 100) {
				progressStatus.textContent = 'Running inference\u2026';
			}
		}
	};

	xhr.onload = () => {
		scanLine.style.display = 'none';
		analyzeBtn.disabled = false;
		analyzeBtn.textContent = 'Analyze sample';
		progressWrap.style.display = 'none';

		let data;
		try {
			data = JSON.parse(xhr.responseText);
		} catch (err) {
			showError('The server returned an unreadable response. Try again.');
			return;
		}

		if (xhr.status >= 200 && xhr.status < 300) {
			renderResults(data);
		} else {
			showError(data.detail || 'Analysis failed. Try a different image.');
		}
	};

	xhr.onerror = () => {
		scanLine.style.display = 'none';
		analyzeBtn.disabled = false;
		analyzeBtn.textContent = 'Analyze sample';
		progressWrap.style.display = 'none';
		showError('Could not reach the server. Check your connection and try again.');
	};

	xhr.send(formData);
}

function renderResults(data) {

	// final result rendering logic



	resultsEmpty.style.display = 'none';
	resultHeader.style.display = 'flex';
	typeGrid.style.display = 'grid';

	resultCall.textContent = data.predicted_class;
	resultConf.textContent = (data.confidence * 100).toFixed(1) + '%';

	typeGrid.innerHTML = '';
	data.probabilities.forEach(item => {

		
		const chip = document.createElement('div');
		chip.className = 'type-chip' + (item.label === data.predicted_class ? ' match' : '');
		const pct = (item.probability * 100).toFixed(1);
		chip.innerHTML = `
        <div class="grp">${item.label}</div>
        <div class="pct">${pct}%</div>
        <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
      `;
		typeGrid.appendChild(chip);
	});
}