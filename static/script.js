// Елементи для відображення результатів
const resultCard = document.getElementById("resultCard");
const scoreEl = document.getElementById("score");
const scoreBar = document.getElementById("scoreBar");
const wpmEl = document.getElementById("wpm");
const parasitesEl = document.getElementById("parasites");
const recognizedEl = document.getElementById("recognized");
const statusEl = document.getElementById("status");

// Функція для оновлення результатів
function updateResults(data) {
  console.log("Оновлення результатів:", data);

  resultCard.style.display = "block";
  scoreEl.innerText = `${data.language_score.toFixed(1)}/10`;
  scoreBar.style.width = `${data.language_score * 10}%`;
  wpmEl.innerText = `${data.words_per_min} слів/хв`;
  parasitesEl.innerText = data.parasite_count;
  recognizedEl.innerText = data.recognized_text || "Текст не розпізнано";
}

// Функція для показу помилки
function showError(element, message) {
  element.innerText = message;
  element.style.color = "#d32f2f";
}

// Функція для показу успіху
function showSuccess(element, message) {
  element.innerText = message;
  element.style.color = "#388e3c";
}

// ===== Аналіз аудіофайлу =====
const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");
const fileStatus = document.getElementById("fileStatus");

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    showError(fileStatus, "Будь ласка, виберіть файл");
    return;
  }

  // Перевірка розміру файлу (макс 50MB)
  if (file.size > 50 * 1024 * 1024) {
    showError(fileStatus, "Файл занадто великий (макс 50MB)");
    return;
  }

  showError(fileStatus, "Обробка файлу...");

  const formData = new FormData();
  formData.append("audio", file);

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `Помилка ${response.status}`);
    }

    updateResults(data);
    showSuccess(fileStatus, "Файл успішно проаналізовано!");

  } catch (error) {
    console.error("Помилка:", error);
    showError(fileStatus, "Помилка: " + error.message);
  }
});

// ===== Аналіз тексту =====
const textForm = document.getElementById("textForm");
const textInput = document.getElementById("textInput");
const textStatus = document.getElementById("textStatus");
const charCount = document.getElementById("charCount");

// Лічильник символів
textInput.addEventListener("input", () => {
  charCount.textContent = textInput.value.length;
  textStatus.innerText = ""; // Очистити статус
});

// Обробка відправки тексту
textForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = textInput.value.trim();
  if (!text) {
    showError(textStatus, "Будь ласка, введіть текст для аналізу");
    return;
  }

  if (text.length < 10) {
    showError(textStatus, "Текст занадто короткий. Мінімум 10 символів.");
    return;
  }

  showError(textStatus, "Аналіз тексту...");

  try {
    const response = await fetch("/analyze-text", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text: text })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `Помилка ${response.status}`);
    }

    updateResults(data);
    showSuccess(textStatus, "Текст успішно проаналізовано!");

  } catch (error) {
    console.error("Помилка:", error);
    showError(textStatus, "Помилка: " + error.message);
  }
});

// ===== Запис аудіо =====
const startBtn = document.getElementById("startBtn");

// Якщо ви хочете додати запис аудіо, додайте цей код:
if (startBtn) {
  let mediaRecorder;
  let audioChunks = [];
  let recordingTimer;

  startBtn.addEventListener("click", async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError(statusEl, "Ваш браузер не підтримує запис аудіо");
      return;
    }

    try {
      if (mediaRecorder && mediaRecorder.state === "recording") {
        // Зупинити запис
        mediaRecorder.stop();
        clearTimeout(recordingTimer);
        startBtn.innerText = "Записати 5 сек";
        return;
      }

      showError(statusEl, "Запит доступу до мікрофона...");

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.webm");

        showError(statusEl, "Обробка запису...");

        try {
          const response = await fetch("/analyze", {
            method: "POST",
            body: formData
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.error || `Помилка ${response.status}`);
          }

          updateResults(data);
          showSuccess(statusEl, "Запис успішно проаналізовано!");

        } catch (error) {
          console.error("Помилка:", error);
          showError(statusEl, "Помилка: " + error.message);
        }
      };

      // Почати запис
      mediaRecorder.start();
      startBtn.innerText = "Зупинити запис";
      showError(statusEl, "Записується... Говоріть!");

      // Автоматично зупинити через 5 секунд
      recordingTimer = setTimeout(() => {
        if (mediaRecorder.state === "recording") {
          mediaRecorder.stop();
          startBtn.innerText = "Записати 5 сек";
        }
      }, 5000);

    } catch (error) {
      console.error("Помилка при доступі до мікрофона:", error);
      showError(statusEl, "Не вдалося отримати доступ до мікрофона");
    }
  });
}