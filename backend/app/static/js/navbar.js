function menu() {
    const menuButton = document.querySelector(".menu");
    const menuList = document.querySelector(".menuList");

    document.body.classList.toggle("no-scroll");
    menuButton.classList.toggle("open");

    if (window.getComputedStyle(menuList).display === "none") {
        menuList.style.display = "block";
    } else {
        menuList.style.display = "none";
    }
}

window.addEventListener("scroll", function () {
    const navbar = document.querySelector(".navbar");

    if (window.scrollY > 50) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});

function toggleLightMode() {
    document.body.classList.toggle("light-mode");
}

window.onscroll = function() {progress()};

function progress() {
  var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
  var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  var scrolled = (winScroll / height) * 100;
  document.getElementById("myBar").style.width = scrolled + "%";
}