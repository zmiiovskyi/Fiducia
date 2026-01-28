const resultCard = document.getElementById("resultCard");
const scoreEl = document.getElementById("score");
const scoreBar = document.getElementById("scoreBar");
const wpmEl = document.getElementById("wpm");
const parasitesEl = document.getElementById("parasites");
const recognizedEl = document.getElementById("recognized");
const statusEl = document.getElementById("status");

function updateResults(data){
  resultCard.style.display="block";
  scoreEl.innerText=`${data.language_score.toFixed(1)}/10`;
  scoreBar.style.width=`${data.language_score*10}%`;
  wpmEl.innerText=`${data.words_per_min} слів/хв`;
  parasitesEl.innerText=data.parasite_count;
  recognizedEl.innerText=data.recognized_text||"Текст не розпізнано";
}

function showError(el,msg){el.innerText=msg;el.style.color="#d32f2f";}
function showSuccess(el,msg){el.innerText=msg;el.style.color="#388e3c";}

// --- Аудіо файл ---
const uploadForm=document.getElementById("uploadForm");
const fileInput=document.getElementById("fileInput");
const fileStatus=document.getElementById("fileStatus");

uploadForm.addEventListener("submit", async e=>{
  e.preventDefault();
  const file=fileInput.files[0];
  if(!file){showError(fileStatus,"Будь ласка, виберіть файл");return;}
  if(file.size>50*1024*1024){showError(fileStatus,"Файл занадто великий (макс 50MB)");return;}
  showError(fileStatus,"Обробка файлу...");
  const formData=new FormData();
  formData.append("audio",file);
  try{
    const res=await fetch("/analyze",{method:"POST",body:formData});
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||`Помилка ${res.status}`);
    updateResults(data); showSuccess(fileStatus,"Файл успішно проаналізовано!");
  }catch(err){console.error(err); showError(fileStatus,"Помилка: "+err.message);}
});

// --- Текст ---
const textForm=document.getElementById("textForm");
const textInput=document.getElementById("textInput");
const textStatus=document.getElementById("textStatus");
const charCount=document.getElementById("charCount");

textInput.addEventListener("input",()=>{charCount.textContent=textInput.value.length;textStatus.innerText="";});
textForm.addEventListener("submit", async e=>{
  e.preventDefault();
  const text=textInput.value.trim();
  if(!text){showError(textStatus,"Будь ласка, введіть текст"); return;}
  if(text.length<10){showError(textStatus,"Текст занадто короткий. Мінімум 10 символів."); return;}
  showError(textStatus,"Аналіз тексту...");
  try{
    const res=await fetch("/analyze-text",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
    const data=await res.json();
    if(!res.ok) throw new Error(data.error||`Помилка ${res.status}`);
    updateResults(data); showSuccess(textStatus,"Текст успішно проаналізовано!");
  }catch(err){console.error(err); showError(textStatus,"Помилка: "+err.message);}
});

// --- Запис аудіо ---
const startBtn=document.getElementById("startBtn");
if(startBtn){
  let mediaRecorder, audioChunks=[], recordingTimer;
  startBtn.addEventListener("click",async ()=>{
    if(!navigator.mediaDevices?.getUserMedia){showError(statusEl,"Браузер не підтримує запис");return;}
    try{
      if(mediaRecorder?.state==="recording"){mediaRecorder.stop(); clearTimeout(recordingTimer); startBtn.innerText="Записати 5 сек"; return;}
      showError(statusEl,"Запит доступу до мікрофона...");
      const stream=await navigator.mediaDevices.getUserMedia({audio:true});
      mediaRecorder=new MediaRecorder(stream); audioChunks=[];
      mediaRecorder.ondataavailable=e=>{if(e.data.size>0) audioChunks.push(e.data);}
      mediaRecorder.onstop=async ()=>{
        const audioBlob=new Blob(audioChunks,{type:'audio/webm'});
        const formData=new FormData(); formData.append("audio",audioBlob,"recording.webm");
        showError(statusEl,"Обробка запису...");
        try{
          const res=await fetch("/analyze",{method:"POST",body:formData});
          const data=await res.json();
          if(!res.ok) throw new Error(data.error||`Помилка ${res.status}`);
          updateResults(data); showSuccess(statusEl,"Запис успішно проаналізовано!");
        }catch(err){console.error(err);showError(statusEl,"Помилка: "+err.message);}
      };
      mediaRecorder.start(); startBtn.innerText="Зупинити запис"; showError(statusEl,"Записується... Говоріть!");
      recordingTimer=setTimeout(()=>{if(mediaRecorder.state==="recording"){mediaRecorder.stop(); startBtn.innerText="Записати 5 сек";}},5000);
    }catch(err){console.error(err);showError(statusEl,"Не вдалося отримати доступ до мікрофона");}
  });
}
