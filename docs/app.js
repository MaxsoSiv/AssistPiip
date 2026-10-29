(() => {
  "use strict";

  const FALLBACK_RELEASES = [
    {
      version: "1.0.1",
      date: "2026-10-24",
      file: "https://github.com/MaxsoSiv/AssistPiip/releases",
      size: 0,
      notes:
        "Обновление 1.0.1:\n" +
        "• Глобальная горячая клавиша (по умолчанию Ctrl+Alt+P, меняется в настройках)\n" +
        "• Автопроверка обновлений и обновление в один клик\n" +
        "• Команда заметок: «заметка купить хлеб» или «заметка текст | описание»\n" +
        "• Напоминания и таймеры с уведомлениями\n" +
        "• Вкладка «Переводчик»\n" +
        "• Улучшенный анимированный фон и плавающий кружок\n" +
        "• Окно растягивается за угол, история команд стрелками\n" +
        "• Исправлен калькулятор: XOR и логические операции в HEX",
    },
    {
      version: "1.0.0",
      date: "2026-10-22",
      file: "https://github.com/MaxsoSiv/AssistPiip/releases/download/Release/AssistPiip-Beta-1.0.0.zip",
      size: 47908596,
      notes:
        "Первый бета-релиз:\n" +
        "• Кастомные команды с алиасами и быстрым доступом\n" +
        "• Буфер обмена: текст и картинки, поиск по дате\n" +
        "• Калькулятор: обычный, инженерный, программистский\n" +
        "• Заметки с закреплением\n" +
        "• 4 темы оформления и анимированный фон\n" +
        "• Сворачивание в плавающий кружок",
    },
  ];

  const yearEl        = document.getElementById("year");
  const heroVersionEl = document.getElementById("hero-version");
  const downloadBtn   = document.getElementById("download-btn");
  const versionInline = document.getElementById("download-version-inline");
  const sizeEl        = document.getElementById("download-size");
  const updatesList   = document.getElementById("updates-list");

  if (yearEl) yearEl.textContent = new Date().getFullYear();

  function humanSize(bytes) {
    if (!bytes || bytes < 0) return "—";
    const units = ["Б", "КБ", "МБ", "ГБ"];
    let i = 0;
    let n = bytes;
    while (n >= 1024 && i < units.length - 1) {
      n /= 1024;
      i++;
    }
    return n.toFixed(n >= 10 || i === 0 ? 0 : 1) + " " + units[i];
  }

  function formatDate(iso) {
    try {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return iso;
      const months = [
        "янв", "фев", "мар", "апр", "май", "июн",
        "июл", "авг", "сен", "окт", "ноя", "дек",
      ];
      return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
    } catch {
      return iso;
    }
  }

  function versionTuple(v) {
    return String(v || "0")
      .split(".")
      .map((p) => parseInt(p, 10) || 0);
  }

  function byVersionDesc(a, b) {
    const ta = versionTuple(a.version);
    const tb = versionTuple(b.version);
    for (let i = 0; i < Math.max(ta.length, tb.length); i++) {
      const d = (tb[i] || 0) - (ta[i] || 0);
      if (d !== 0) return d;
    }
    return 0;
  }

  async function loadReleases() {
    if (location.protocol === "file:") {
      return FALLBACK_RELEASES;
    }
    try {
      const resp = await fetch("releases.json", { cache: "no-store" });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      if (!Array.isArray(data) || !data.length) {
        throw new Error("Пустой releases.json");
      }
      return data.slice().sort(byVersionDesc);
    } catch (err) {
      console.warn("releases.json не загрузился, использую встроенные данные:", err);
      return FALLBACK_RELEASES.slice().sort(byVersionDesc);
    }
  }

  function renderHero(releases) {
    if (!heroVersionEl || !releases.length) return;
    const latest = releases[0];
    heroVersionEl.textContent =
      `Версия ${latest.version} · ${formatDate(latest.date)}`;
  }

  function renderDownload(releases) {
    if (!releases.length) return;
    const latest = releases[0];

    if (versionInline) versionInline.textContent = "v" + latest.version;
    if (downloadBtn) {
      downloadBtn.href = latest.file;
      downloadBtn.setAttribute("download", "");
    }
    if (sizeEl) sizeEl.textContent = humanSize(latest.size);
  }

  const verRail = document.getElementById("version-rail");
  const verPrev = document.getElementById("ver-prev");
  const verNext = document.getElementById("ver-next");
  let currentRelease = 0;
  let allReleases = [];

  function selectRelease(index) {
    if (!allReleases.length) return;
    currentRelease = Math.max(0, Math.min(index, allReleases.length - 1));
    renderRail();
    renderDetail();
  }

  function renderRail() {
    if (!verRail) return;
    verRail.replaceChildren();
    allReleases.forEach((r, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ver-chip" + (i === currentRelease ? " is-active" : "");
      const ver = document.createElement("span");
      ver.className = "ver-chip-version";
      ver.textContent = "v" + r.version;
      const date = document.createElement("span");
      date.className = "ver-chip-date";
      date.textContent = formatDate(r.date);
      btn.append(ver, date);
      btn.addEventListener("click", () => selectRelease(i));
      verRail.append(btn);
    });
    const active = verRail.querySelector(".is-active");
    if (active) active.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
  }

  function renderDetail() {
    if (!updatesList || !allReleases.length) return;
    const r = allReleases[currentRelease];

    updatesList.replaceChildren();

    const row = document.createElement("div");
    row.className = "release";

    const left = document.createElement("div");
    const ver = document.createElement("div");
    ver.className = "release-version";
    ver.textContent = "v" + r.version;
    if (currentRelease === 0) {
      const badge = document.createElement("span");
      badge.className = "release-current";
      badge.textContent = "актуальная";
      ver.append(badge);
    }
    left.append(ver);

    const date = document.createElement("span");
    date.className = "release-date";
    date.textContent = formatDate(r.date);
    left.append(date);

    const counter = document.createElement("span");
    counter.className = "release-counter";
    counter.textContent = (currentRelease + 1) + " / " + allReleases.length;
    left.append(counter);

    const body = document.createElement("div");
    body.className = "release-body";
    body.textContent = r.notes || "—";

    if (r.file) {
      const link = document.createElement("a");
      link.className = "release-download";
      link.href = r.file;
      link.setAttribute("download", "");
      link.innerHTML =
        '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" ' +
        'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M10 3v10M5 9l5 5 5-5M4 17h12"/></svg>' +
        "Скачать v" + r.version;
      body.append(document.createElement("br"));
      body.append(link);
    }

    row.append(left, body);
    updatesList.append(row);

    if (verPrev) verPrev.disabled = currentRelease === 0;
    if (verNext) verNext.disabled = currentRelease === allReleases.length - 1;
  }

  function renderReleases(releases) {
    allReleases = releases;
    currentRelease = 0;
    renderRail();
    renderDetail();
    observeReveals();
  }
  function setupReveals() {
    const targets = document.querySelectorAll(
      ".section-title, .feature, .screenshot-frame, .spec, .faq-item, .legal"
    );
    targets.forEach(el => el.classList.add("reveal"));
    observeReveals();
  }

  function observeReveals() {
    const items = document.querySelectorAll(".reveal:not(.is-visible)");
    if (!items.length) return;

    if (!("IntersectionObserver" in window)) {
      items.forEach(el => el.classList.add("is-visible"));
      return;
    }

    if (!observeReveals._io) {
      observeReveals._io = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            obs.unobserve(entry.target);
          }
        });
      }, {
        rootMargin: "0px 0px -8% 0px",
        threshold: 0.05,
      });
    }

    const io = observeReveals._io;
    items.forEach(el => {
      const siblings = el.parentElement
        ? Array.from(el.parentElement.children).indexOf(el)
        : 0;
      if (siblings > 0 && siblings < 8) {
        el.style.transitionDelay = (siblings * 40) + "ms";
      }
      io.observe(el);
    });
  }

  function setupScrollProgress() {
    const nav = document.querySelector(".nav");
    if (!nav) return;

    const update = () => {
      const h = document.documentElement;
      const max = h.scrollHeight - h.clientHeight;
      const ratio = max > 0 ? (h.scrollTop / max) * 100 : 0;
      nav.style.setProperty("--scroll-progress", ratio.toFixed(2) + "%");
    };

    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  (async () => {
    setupReveals();
    setupScrollProgress();

    if (verPrev) verPrev.addEventListener("click", () => selectRelease(currentRelease - 1));
    if (verNext) verNext.addEventListener("click", () => selectRelease(currentRelease + 1));

    const releases = await loadReleases();
    renderHero(releases);
    renderDownload(releases);
    renderReleases(releases);
  })();
})();
