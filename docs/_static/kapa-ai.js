document.addEventListener("DOMContentLoaded", function () {
  var script = document.createElement("script");
  script.src = "https://widget.kapa.ai/kapa-widget.bundle.js";
  script.setAttribute("data-website-id", "08e64dae-cea6-4fbc-8207-1c8bd260a14c");
  script.setAttribute("data-project-name", "django CMS");
  script.setAttribute("data-project-color", "#A1C42C");
  script.setAttribute("data-modal-title", "django CMS AI Bot - ask me anything!");

  script.setAttribute("data-modal-size", "80%");
  script.setAttribute("data-modal-image-hide", "true");
  script.setAttribute("data-modal-disclaimer", "This is a custom LLM for django CMS trained on publicly available data such as django CMS' technical documentation. Sponsored by kapa.ai");

  script.setAttribute("data-button-height", "3em");
  script.setAttribute("data-button-width", "4em");

  // top right placement conflicts with text on some pages as well,
  // so I chose the bottom right position as this is a dominant design pattern
  // script.setAttribute("data-button-position-top", "10px");
  // script.setAttribute("data-button-position-right", "10px");
  script.setAttribute("data-button-image", "https://www.django-cms.org/static/img/django-logo.svg");
  script.setAttribute("data-button-image-height", "11");
  script.setAttribute("data-button-image-width", "60");
  script.setAttribute("data-button-text-shadow", "none");

  script.async = true;
  document.head.appendChild(script);
});
