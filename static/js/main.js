/**
 * EventHub — shared UI behaviors
 * Accordion, tabs, modals, sidebar, flash dismiss
 */
(function () {
  "use strict";

  /* Sidebar toggle (desktop collapse + mobile) */
  var sidebar = document.getElementById("sidebar");
  var toggle = document.getElementById("sidebarToggle");
  var backdrop = document.getElementById("sidebarBackdrop");
  var layoutMain = document.querySelector(".layout-main");

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("open");
    if (backdrop) backdrop.hidden = true;
  }

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("open");
    if (backdrop) backdrop.hidden = false;
  }

  function toggleSidebarCollapse() {
    if (!sidebar) return;

    // On desktop, toggle collapsed state
    if (window.innerWidth > 900) {
      sidebar.classList.toggle("collapsed");

      // Adjust main content margin
      if (layoutMain) {
        if (sidebar.classList.contains("collapsed")) {
          layoutMain.style.marginLeft = "72px";
        } else {
          layoutMain.style.marginLeft = "240px";
        }
      }
    } else {
      // On mobile, toggle open/close
      if (sidebar.classList.contains("open")) closeSidebar();
      else openSidebar();
    }
  }

  if (toggle && sidebar) {
    toggle.addEventListener("click", toggleSidebarCollapse);
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeSidebar);
  }

  function syncSidebar() {
    if (!sidebar) return;
    if (window.innerWidth <= 900) {
      sidebar.classList.remove("collapsed");
      if (layoutMain) layoutMain.style.marginLeft = "";
    } else closeSidebar();
    if (toggle) toggle.setAttribute("aria-expanded", String(window.innerWidth > 900 ? !sidebar.classList.contains("collapsed") : sidebar.classList.contains("open")));
  }
  if (sidebar) sidebar.querySelectorAll(".nav-link").forEach(function (link) {
    link.setAttribute("aria-label", link.textContent.trim());
    link.title = link.textContent.trim();
    if (!link.querySelector("svg")) link.classList.add("text-only");
    if (link.classList.contains("active")) link.setAttribute("aria-current", "page");
  });
  if (toggle) { toggle.setAttribute("aria-controls", "sidebar"); toggle.addEventListener("click", syncSidebar); }
  window.addEventListener("resize", syncSidebar);
  document.addEventListener("keydown", function (event) { if (event.key === "Escape") { closeSidebar(); syncSidebar(); } });
  syncSidebar();

  /* Accordion */
  document.querySelectorAll("[data-accordion]").forEach(function (root) {
    root.querySelectorAll(".accordion-trigger").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var panel = btn.nextElementSibling;
        var open = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", open ? "false" : "true");
        if (panel) {
          if (open) panel.setAttribute("hidden", "");
          else panel.removeAttribute("hidden");
        }
      });
    });
  });

  /* Tabs */
  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    var tabs = root.querySelectorAll(".tab");
    var panels = root.querySelectorAll(".tab-panel");

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        var id = tab.getAttribute("data-tab");
        tabs.forEach(function (t) {
          t.classList.toggle("active", t === tab);
        });
        panels.forEach(function (p) {
          var match = p.getAttribute("data-panel") === id;
          p.classList.toggle("active", match);
          if (match) p.removeAttribute("hidden");
          else p.setAttribute("hidden", "");
        });
      });
    });
  });

  /* Modals */
  function openModal(id) {
    var modal = document.getElementById(id);
    if (!modal) return;
    modal._opener = document.activeElement;
    modal.removeAttribute("hidden");
    var panel = modal.querySelector(".modal-panel");
    var heading = modal.querySelector("h2");
    if (panel) {
      panel.tabIndex = -1;
      if (heading) { heading.id = heading.id || id + "Title"; panel.setAttribute("aria-labelledby", heading.id); }
      panel.focus();
    }
    document.body.style.overflow = "hidden";
  }

  function closeModal(modal) {
    if (!modal) return;
    modal.setAttribute("hidden", "");
    document.body.style.overflow = "";
    if (modal._opener) modal._opener.focus();
  }

  document.querySelectorAll("[data-modal-open]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      openModal(btn.getAttribute("data-modal-open"));
    });
  });

  document.querySelectorAll(".modal").forEach(function (modal) {
    modal.querySelectorAll("[data-modal-close]").forEach(function (el) {
      el.addEventListener("click", function () {
        closeModal(modal);
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Tab" && !modal.hidden) {
        var controls = Array.from(modal.querySelectorAll('button, input, select, textarea, a[href], [tabindex="0"]')).filter(function (el) { return !el.disabled && el.getClientRects().length; });
        var first = controls[0], last = controls[controls.length - 1];
        if (!first) { e.preventDefault(); }
        else if (e.shiftKey && (document.activeElement === first || document.activeElement === modal.querySelector('.modal-panel'))) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
      if (e.key === "Escape" && !modal.hasAttribute("hidden")) {
        closeModal(modal);
      }
    });
  });

  /* Simple client-side required validation hint */
  document.querySelectorAll("form[novalidate]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!form.checkValidity()) {
        e.preventDefault();
        form.reportValidity();
      }
    });
  });
})();
