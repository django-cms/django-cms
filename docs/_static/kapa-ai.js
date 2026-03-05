document.addEventListener("DOMContentLoaded", function () {
	var button = document.createElement("button");
	button.id = "kapa-ai-button";
	button.type = "button";
	button.textContent = "Ask AI";
	button.setAttribute("aria-label", "Open Django CMS chat");

	button.addEventListener("click", function () {
		window.location.href = "https://chat.django-cms.org/";
	});

	document.body.appendChild(button);
});
