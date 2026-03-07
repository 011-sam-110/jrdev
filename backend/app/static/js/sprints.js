document.querySelectorAll(".stepChoice a").forEach(link => {
    link.addEventListener("click", function(e) {
        document.querySelectorAll(".stepChoice a").forEach(el => {
            el.removeAttribute("id");
        });

        this.id = "currentStep";
    });
});