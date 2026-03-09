const titles = {
    1: "Define Your Vision",
    2: "Developer Screening & Confidentiality",
    3: "Rapid Development Sprint Begins",
    4: "Review"
};

const desc = {
    1: "Drop a brief. We match you with developers who fit your tech stack—typically within 24 hours.",
    2: "View developers who have applied and onboard the right fit with a signed contract. Developers cannot see the deliverables — only the technologies required.",
    3: "As soon as a developer has signed the JrDev approved contract, they have until the end of the deadline to meet your essential deliverables.",
    4: "Review your developer's work through JrDev. If the work does not meet the given essential deliverables, receive a full refund. If you wish to continue work with a developer, you can reach out privately."
};

document.querySelectorAll(".stepChoice a").forEach(link => {
    link.addEventListener("click", function(e) {
        e.preventDefault();

        document.querySelectorAll(".stepChoice a").forEach(el => {
            el.removeAttribute("id");
        });

        this.id = "currentStep";

        const step = this.dataset.step;
        const img = document.getElementById("stepImage");
        const stepNum = document.querySelector(".stepNum");
        const header = document.querySelector(".stepText h1");
        const paragraph = document.querySelector(".stepDesc");

        img.src = `/static/images/Step ${step}.png`;
        stepNum.textContent = `Step ${step}`;
        header.textContent = titles[step];
        paragraph.textContent = desc[step];
    });
});