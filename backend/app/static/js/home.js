(function() {
  'use strict';

  var tablist = document.querySelector('.sprint-tablist');
  if (!tablist) return;

  var tabs = tablist.querySelectorAll('.sprint-tab');
  var panels = document.querySelectorAll('.sprint-panel');

  function setActive(index) {
    var i;
    var wasHidden = panels[index] && panels[index].classList.contains('sprint-panel--hidden');
    for (i = 0; i < tabs.length; i++) {
      tabs[i].setAttribute('aria-selected', i === index ? 'true' : 'false');
      tabs[i].classList.toggle('sprint-tab--active', i === index);
    }
    for (i = 0; i < panels.length; i++) {
      panels[i].classList.toggle('sprint-panel--hidden', i !== index);
      if (i === index && wasHidden) {
        panels[i].classList.add('sprint-panel-enter');
        setTimeout(function(panel) {
          return function() { panel.classList.remove('sprint-panel-enter'); };
        }(panels[i]), 350);
      }
    }
  }

  tabs.forEach(function(tab, index) {
    tab.addEventListener('click', function() {
      setActive(index);
    });
    tab.addEventListener('keydown', function(e) {
      var next;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault();
        next = index < tabs.length - 1 ? index + 1 : 0;
        setActive(next);
        tabs[next].focus();
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault();
        next = index > 0 ? index - 1 : tabs.length - 1;
        setActive(next);
        tabs[next].focus();
      } else if (e.key === 'Home') {
        e.preventDefault();
        setActive(0);
        tabs[0].focus();
      } else if (e.key === 'End') {
        e.preventDefault();
        setActive(tabs.length - 1);
        tabs[tabs.length - 1].focus();
      }
    });
  });

  setActive(0);
})();
