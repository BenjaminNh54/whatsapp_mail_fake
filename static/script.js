let group = null;
let recorder = null;
let chunks = [];
let isPlayingAudio = false;
let lastCount = 0;

// ---------------- OUVRIR UN GROUPE ----------------
function openGroup(id) {
    group = id;
    lastCount = 0;
    document.getElementById("msgs").innerHTML = "";
    load();
}

// ---------------- CHARGER LES NOUVEAUX MSGS ----------------
function load() {
    if (!group || isPlayingAudio) return;

    fetch("/msgs/" + group)
    .then(r => r.json())
    .then(d => {
        let box = document.getElementById("msgs");

        // Ajouter uniquement les nouveaux messages
        for (let i = lastCount; i < d.length; i++) {
            let m = d[i];
            let div = document.createElement("div");
            div.className = "msg";

            let html = `<b>${m[0]}</b>: `;
            if (m[1]) html += m[1];

            if (m[2]) {
                if (m[2].endsWith(".webm")) {
                    html += `<br>
                    <audio controls
                        onplay="isPlayingAudio=true"
                        onpause="isPlayingAudio=false"
                        onended="isPlayingAudio=false"
                        src="/uploads/${m[2]}"></audio>`;
                } else {
                    html += ` <a href="/uploads/${m[2]}" target="_blank">📎</a>`;
                }
            }

            div.innerHTML = html;
            box.appendChild(div);
        }

        if (d.length > lastCount) {
            box.scrollTop = box.scrollHeight;
            lastCount = d.length;
        }
    });
}

// Refresh automatique
setInterval(load, 1500);

// ---------------- ENVOI TEXTE / FICHIER ----------------
document.getElementById("sendForm").onsubmit = e => {
    e.preventDefault();
    if (!group) return;

    let fd = new FormData();
    if (msg.value.trim()) fd.append("msg", msg.value);
    fd.append("group", group);

    if (file.files.length > 0) {
        fd.append("file", file.files[0]);
        file.value = "";
    }

    fetch("/send", { method: "POST", body: fd })
        .then(() => load());

    msg.value = "";
};

// ---------------- VOCAL APPUI / RELÂCHE ----------------
const mic = document.getElementById("mic");

mic.onmousedown = mic.ontouchstart = e => {
    e.preventDefault();
    if (!group) return;

    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        chunks = [];
        recorder = new MediaRecorder(stream);
        recorder.ondataavailable = e => chunks.push(e.data);
        recorder.start();
        mic.innerText = "🔴";
    })
    .catch(() => alert("Accès micro refusé"));
};

mic.onmouseup = mic.ontouchend = e => {
    e.preventDefault();
    if (!recorder) return;

    recorder.stop();
    mic.innerText = "🎤";

    recorder.onstop = () => {
        let blob = new Blob(chunks, { type: "audio/webm" });
        let audioFile = new File([blob], "vocal_" + Date.now() + ".webm");

        let fd = new FormData();
        fd.append("group", group);
        fd.append("file", audioFile);

        fetch("/send", { method: "POST", body: fd })
            .then(() => load());
    };
};