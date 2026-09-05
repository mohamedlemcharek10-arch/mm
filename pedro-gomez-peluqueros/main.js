(function () {
  "use strict";

  const data = window.__BRAND__ || {};
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fineHover = matchMedia("(hover: hover) and (pointer: fine)").matches;

  const $ = (sel, scope) => (scope || document).querySelector(sel);
  const $$ = (sel, scope) => Array.from((scope || document).querySelectorAll(sel));

  function safe(fn, name) {
    try { fn(); } catch (e) { console.warn("[" + name + "]", e); }
  }

  /* ---------------------------------------------------------
     Nav: solidify on scroll
  --------------------------------------------------------- */
  function initNav() {
    const nav = $("[data-nav]");
    if (!nav) return;
    const on = () => nav.classList.toggle("is-scrolled", scrollY > 40);
    on();
    window.addEventListener("scroll", on, { passive: true });
  }

  /* ---------------------------------------------------------
     Mobile hamburger menu
  --------------------------------------------------------- */
  function initMobileNav() {
    const burger = $("[data-nav-burger]");
    const panel = $("[data-nav-mobile]");
    if (!burger || !panel) return;

    function setOpen(open) {
      burger.setAttribute("aria-expanded", String(open));
      panel.dataset.open = String(open);
      panel.setAttribute("aria-hidden", String(!open));
      document.body.style.overflow = open ? "hidden" : "";
    }

    burger.addEventListener("click", () => {
      setOpen(burger.getAttribute("aria-expanded") !== "true");
    });

    $$("a, [data-close-nav]", panel).forEach(el => {
      el.addEventListener("click", () => setOpen(false));
    });

    window.addEventListener("keydown", e => {
      if (e.key === "Escape") setOpen(false);
    });
  }

  /* ---------------------------------------------------------
     Reveal on scroll (universal)
  --------------------------------------------------------- */
  function initReveals() {
    const els = $$("[data-reveal]").filter(el => !el.hasAttribute("data-split"));
    if (!els.length) return;
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add("is-revealed");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.01, rootMargin: "0px 0px -2% 0px" });
    els.forEach(el => io.observe(el));

    setTimeout(() => {
      $$("[data-reveal]:not(.is-revealed)").forEach(el => {
        if (el.getBoundingClientRect().top < innerHeight) el.classList.add("is-revealed");
      });
    }, 6000);
  }

  /* ---------------------------------------------------------
     Hero title split + entrance (above the fold — runs on boot)
  --------------------------------------------------------- */
  function splitWords(el) {
    el.setAttribute("aria-label", el.textContent.trim().replace(/\s+/g, " "));
    const wrap = text => text.split(/(\s+)/).map(w =>
      /^\s+$/.test(w) ? w : `<span class="split-word" aria-hidden="true">${w}</span>`
    ).join("");
    const html = Array.from(el.childNodes).map(node => {
      if (node.nodeType === 3) return wrap(node.textContent);
      if (node.nodeName === "BR") return "<br>";
      if (node.nodeType === 1) {
        const tag = node.tagName.toLowerCase();
        return `<${tag}>${wrap(node.textContent)}</${tag}>`;
      }
      return "";
    }).join("");
    el.innerHTML = html;
    return el.querySelectorAll(".split-word");
  }

  function initHeroSplit() {
    const el = $("[data-split='words']");
    if (!el) return;
    const words = splitWords(el);
    el.classList.add("reveal-ready");
    if (window.gsap) {
      gsap.to(words, {
        opacity: 1, y: 0, duration: 0.9, stagger: 0.05, ease: "expo.out", delay: 0.15,
      });
    } else {
      requestAnimationFrame(() => words.forEach(w => { w.style.opacity = 1; w.style.transform = "none"; }));
    }
  }

  /* ---------------------------------------------------------
     Subtle 3D tilt on cards (desktop, fine pointer only)
  --------------------------------------------------------- */
  function initTilt() {
    if (!fineHover) return;
    $$(".service-card, .gallery-item, .testimonial-card").forEach(card => {
      const MAX = 6;
      let tx = 0, ty = 0, cx = 0, cy = 0, raf = null;
      card.classList.add("has-tilt");
      card.addEventListener("mousemove", e => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        tx = -py * MAX; ty = px * MAX;
        if (!raf) raf = requestAnimationFrame(loop);
      });
      card.addEventListener("mouseleave", () => { tx = 0; ty = 0; if (!raf) raf = requestAnimationFrame(loop); });
      function loop() {
        cx += (tx - cx) * 0.16; cy += (ty - cy) * 0.16;
        card.style.setProperty("--rx", cx.toFixed(2) + "deg");
        card.style.setProperty("--ry", cy.toFixed(2) + "deg");
        raf = (Math.abs(tx - cx) > 0.05 || Math.abs(ty - cy) > 0.05) ? requestAnimationFrame(loop) : null;
      }
    });
  }

  /* ---------------------------------------------------------
     Hero parallax (GSAP + ScrollTrigger, optional enhancement)
  --------------------------------------------------------- */
  function initHeroParallax() {
    if (!window.gsap || !window.ScrollTrigger || reduced) return;
    const bg = $(".hero-bg");
    if (!bg) return;
    gsap.to(bg, {
      yPercent: 14, ease: "none",
      scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true },
    });
  }

  /* ---------------------------------------------------------
     Contact form -> builds WhatsApp message (no backend)
  --------------------------------------------------------- */
  function setupContactForm() {
    const form = $("[data-contact-form]");
    const success = $("[data-contact-success]");
    if (!form || !success) return;
    const msg = $("[data-contact-success-msg]");

    form.addEventListener("submit", e => {
      e.preventDefault();
      if (form.classList.contains("is-sending") || form.classList.contains("is-sent")) return;
      if (!form.reportValidity()) return;

      form.classList.add("is-sending");

      const name = form.elements.name.value.trim();
      const phone = form.elements.phone.value.trim();
      const service = form.elements.service.value.trim();
      const message = form.elements.message.value.trim();

      const lines = [
        "Hola, quiero pedir cita en Pedro Gómez Peluqueros.",
        "Nombre: " + name,
        "Teléfono: " + phone,
        "Servicio: " + service,
      ];
      if (message) lines.push("Mensaje: " + message);

      const waNumber = (data.whatsappNumber || "34955229520");
      const waUrl = "https://wa.me/" + waNumber + "?text=" + encodeURIComponent(lines.join("\n"));

      setTimeout(() => {
        form.classList.remove("is-sending");
        form.classList.add("is-sent");
        const firstName = name.split(/\s+/)[0] || "";
        if (msg) msg.textContent = (firstName ? firstName + ", " : "") + "te llevamos a WhatsApp para confirmar tu cita.";
        success.setAttribute("aria-hidden", "false");
        window.open(waUrl, "_blank", "noopener");
      }, 550);
    });
  }

  /* ---------------------------------------------------------
     Footer year
  --------------------------------------------------------- */
  function initFooterYear() {
    const el = $("[data-year]");
    if (el) el.textContent = String(new Date().getFullYear());
  }

  function boot() {
    safe(initNav, "initNav");
    safe(initMobileNav, "initMobileNav");
    safe(initHeroSplit, "initHeroSplit");
    safe(initReveals, "initReveals");
    safe(initTilt, "initTilt");
    safe(setupContactForm, "setupContactForm");
    safe(initFooterYear, "initFooterYear");

    if (window.gsap && window.ScrollTrigger) {
      try { gsap.registerPlugin(ScrollTrigger); } catch (_) {}
      safe(initHeroParallax, "initHeroParallax");
    }

    document.documentElement.classList.add("is-ready");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
