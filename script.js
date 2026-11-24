const MASTER_PHONE = '77715442786';
const MASTER_PHONE_DISPLAY = '+7 771 544 27 86';
const API_URL = 'https://ВАШ-СЕРВИС.onrender.com/api/lead';

const citySelect = document.getElementById('citySelect');
const customDistrictGroup = document.getElementById('customDistrictGroup');
const customDistrictInput = document.getElementById('customDistrict');
const sourceSelect = document.getElementById('source');
const entryForm = document.getElementById('entryForm');
const welcomeModal = document.getElementById('welcomeModal');
const siteWrapper = document.getElementById('siteWrapper');
const displayLocation = document.getElementById('displayLocation');
const callbackForm = document.getElementById('callbackForm');
const callSummary = document.getElementById('callSummary');
const whatsappBtn = document.getElementById('whatsappBtn');

let selectedLocation = 'Алматы и Алатау';
let selectedSource = 'Не указан';

citySelect.addEventListener('change', function() {
    if (this.value === 'other_district') {
        customDistrictGroup.style.display = 'block';
        customDistrictInput.required = true;
    } else {
        customDistrictGroup.style.display = 'none';
        customDistrictInput.required = false;
        customDistrictInput.value = '';
    }
});

entryForm.addEventListener('submit', function(e) {
    e.preventDefault();
    selectedLocation = citySelect.value === 'other_district'
        ? customDistrictInput.value.trim()
        : citySelect.value;
    selectedSource = sourceSelect.value;

    displayLocation.textContent = 'Локация: ' + selectedLocation;

    const welcomeText = encodeURIComponent(
        `Здравствуйте! Нужен ремонт газового котла. Локация: ${selectedLocation}. Источник: ${selectedSource}.`
    );
    whatsappBtn.href = `https://wa.me/${MASTER_PHONE}?text=${welcomeText}`;

    welcomeModal.style.display = 'none';
    siteWrapper.style.display = 'block';
});

callbackForm.addEventListener('submit', function(e) {
    e.preventDefault();

    const name = document.getElementById('clientName').value.trim();
    const phone = document.getElementById('clientPhone').value.trim();
    const model = document.getElementById('boilerModel').value.trim() || 'не указана';

    const message =
        `Новый вызов на ${MASTER_PHONE_DISPLAY}:\n` +
        `Клиент: ${name}\n` +
        `Телефон: ${phone}\n` +
        `Локация: ${selectedLocation}\n` +
        `Котёл: ${model}\n` +
        `Источник: ${selectedSource}`;

    const waUrl = `https://wa.me/${MASTER_PHONE}?text=${encodeURIComponent(message)}`;

    fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name: name,
            phone: phone,
            model: model,
            location: selectedLocation,
            source: selectedSource,
            masterPhone: MASTER_PHONE_DISPLAY
        })
    })
    .then(function(res) {
        if (!res.ok) {
            throw new Error('Ошибка сервера');
        }
        return res.json();
    })
    .then(function() {
        callSummary.style.display = 'block';
        callSummary.innerHTML =
            `<p style="color: #22c55e;"><strong>Заявка отправлена!</strong></p>` +
            `<p>Ожидайте звонка мастера на номер ${phone}.</p>` +
            `<div class="summary-actions">` +
            `<a href="tel:+${MASTER_PHONE}" class="btn-primary">Позвонить сразу</a>` +
            `<a href="${waUrl}" target="_blank" rel="noopener noreferrer" class="btn-secondary">Написать в WhatsApp</a>` +
            `</div>`;
    })
    .catch(function() {
        callSummary.style.display = 'block';
        callSummary.innerHTML =
            `<p style="color: #ef4444;">Сервер не ответил. Можно сразу отправить заявку в WhatsApp:</p>` +
            `<div class="summary-actions">` +
            `<a href="${waUrl}" target="_blank" rel="noopener noreferrer" class="btn-primary">Открыть WhatsApp</a>` +
            `<a href="tel:+${MASTER_PHONE}" class="btn-secondary">Позвонить</a>` +
            `</div>`;
    });

    callbackForm.reset();
});