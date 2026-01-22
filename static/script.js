const startBtn = document.getElementById("startBtn");
const status = document.getElementById("status");
const resultCard = document.getElementById("resultCard");

const scoreEl = document.getElementById("score");
const scoreBar = document.getElementById("scoreBar");
const wpmEl = document.getElementById("wpm");
const parasitesEl = document.getElementById("parasites");
const recognizedEl = document.getElementById("recognized");

startBtn.onclick = async () => {
  status.innerText = "Запис...";

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  let chunks = [];

  mediaRecorder.ondataavailable = (e) => {
    chunks.push(e.data);
  };

  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, { type: "audio/webm" });
    const file = new File([blob], "voice.webm", { type: "audio/webm" });

    const formData = new FormData();
    formData.append("audio", file);
    formData.append("duration", 5);

    status.innerText = "Обробка...";

    const res = await fetch("/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    // Вивід
    resultCard.style.display = "block";
    scoreEl.innerText = `${data.language_score}/10`;
    scoreBar.style.width = `${data.language_score * 10}%`;
    wpmEl.innerText = `${data.words_per_min} слів/хв`;
    parasitesEl.innerText = data.parasite_count;
    recognizedEl.innerText = data.recognized_text;

    status.innerText = "Готово!";
  };

  mediaRecorder.start();

  setTimeout(() => {
    mediaRecorder.stop();
    stream.getTracks().forEach(t => t.stop());
  }, 5000);
};
