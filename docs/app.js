(() => {
  "use strict";

  const FALLBACK_RELEASES = [
    {
      version: "1.0.0",
      date: "2026-10-24",
      file: "releases/AssistPiip-Beta-1.0.0.zip",
      size: 0,
      notes:
        "Первый бета-релиз. Что внутри:\n" +
        "• Кастомные команды с алиасами и быстрым доступом\n" +
        "• Буфер обмена (хранит текст и картинки, есть поиск по дате)\n" +
        "• Встроенный калькулятор (обычный, инженерный, программистский)\n" +
        "• Заметки с закреплением\n" +
        "• 4 темы: Тёмная, Светлая, Закат, Океан\n" +
        "• Анимированный фон в главном меню\n" +
        "• Сворачивание в плавающий кружок\n\n" +
        "Работает локально. Если найдёте баг — пишите на почту. Приятного пользования!",
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
      return data;
    } catch (err) {
      console.warn("releases.json не загрузился, использую встроенные данные:", err);
      return FALLBACK_RELEASES;
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

  function renderReleases(releases) {
    if (!updatesList) return;
    updatesList.replaceChildren();

    if (!releases.length) {
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = "Пока нет записей.";
      updatesList.append(p);
      return;
    }

    releases.forEach((r, index) => {
      const row = document.createElement("div");
      row.className = "release reveal";

      const left = document.createElement("div");
      const ver = document.createElement("div");
      ver.className = "release-version";
      ver.textContent = r.version;
      if (index === 0) {
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
          "Скачать";
        body.append(document.createElement("br"));
        body.append(link);
      }

      row.append(left, body);
      updatesList.append(row);
    });

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

    const releases = await loadReleases();
    renderHero(releases);
    renderDownload(releases);
    renderReleases(releases);
  })();
})();
