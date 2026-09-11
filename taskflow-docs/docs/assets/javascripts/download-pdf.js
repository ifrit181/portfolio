/* Кнопка «Скачать страницу в PDF»: качает пред-сгенерированный PDF
   для текущей страницы из <site>/assets/pdf/<маппинг>.pdf */

(function () {
  "use strict";

  var btn = document.getElementById("powerstore");

  function siteRoot() {
    var cfg;
    try {
      cfg = JSON.parse(document.getElementById("__config").textContent);
    } catch (e) {
      cfg = { base: "." };
    }
    return new URL(cfg.base || ".", document.baseURI).pathname.replace(/\/+$/, "");
  }

  function currentMd() {
    var root = siteRoot();
    var rel = window.location.pathname;
    if (root && rel.indexOf(root) === 0) {
      rel = rel.slice(root.length);
    }
    rel = rel.replace(/\/$/, "").replace(/^\//, "");
    if (rel === "" || rel.endsWith("/index.html")) {
      rel = "index";
    } else if (rel.endsWith(".html")) {
      rel = rel.slice(0, -5);
    }
    return rel + ".md";
  }

  function init() {
    if (!btn) {
      return;
    }
    var md = currentMd();
    var url = siteRoot() + "/assets/pdf/" + md.replace(/\.md$/, ".pdf");

    fetch(url, { method: "HEAD" }).then(function (resp) {
      btn.hidden = !resp.ok;
      if (!resp.ok) {
        console.warn("PDF not found:", url);
      }
    }).catch(function () {
      btn.hidden = true;
    });

    btn.addEventListener("click", function (ev) {
      ev.preventDefault();
      fetch(url).then(function (resp) {
        if (!resp.ok) {
          throw new Error(url + " -> " + resp.status);
        }
        return resp.blob();
      }).then(function (blob) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = md.replace(/\.md$/, ".pdf");
        document.body.appendChild(a);
        a.click();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        a.remove();
      }).catch(function (err) {
        console.warn("PDF download failed:", err);
        btn.hidden = true;
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();