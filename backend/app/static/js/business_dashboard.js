/**
 * Business Dashboard – modular UI logic (deliverables, technologies, sliders, launch form).
 * Preserves all existing behavior; no features removed.
 */

(function () {
  'use strict';

  const DEFAULT_DEVS = 3;
  const DEFAULT_PER_DEV = 20;
  const DEFAULT_TIMELINE_DAYS = 7;
  const DEFAULT_MIN_REQUIREMENTS = 1;

  const TAG_BASE_CLASS = 'tech-tag flex items-center gap-2 px-3 py-1.5 bg-navy-700/50 border border-white/10 rounded-lg text-xs font-medium text-slate-300';

  /**
   * Resolve all dashboard DOM elements once.
   * @returns {Object} Refs to inputs, lists, sliders, forms.
   */
  function getDOMElements() {
    const reqInput = document.getElementById('requirement-buffet-input');
    const techInput = document.getElementById('technologies-required-input');
    const techList = document.getElementById('technologies-tags-list');
    const devSlider = document.querySelector('input[type="range"][max="5"]');
    const timelineSlider = document.querySelector('.sprint-timeline-slider');
    const investmentPerDevSlider = document.querySelector('.investment-per-dev-slider');
    const minReqSlider = document.querySelector('.min-requirements-slider');
    const postContractForm = document.getElementById('post-contract-form');
    const launchForm = document.getElementById('launch-sprint-form');

    return {
      reqInput,
      reqAddBtn: reqInput?.nextElementSibling,
      reqList: reqInput?.parentElement?.nextElementSibling,
      techInput,
      techAddBtn: document.getElementById('technologies-add-btn'),
      techList,
      devSlider,
      devCount: devSlider?.previousElementSibling?.querySelector('span.text-2xl'),
      timelineSlider,
      timelineDays: document.querySelector('.timeline-days'),
      investmentPerDevSlider,
      investmentPerDevDisplay: document.querySelector('.investment-per-dev'),
      minReqSlider,
      minReqDisplay: document.querySelector('.min-requirements-display'),
      investmentAmount: document.querySelector('.investment-amount'),
      postContractForm,
      launchForm,
    };
  }

  /**
   * Create a removable tag element with optional custom class.
   * @param {string} text - Label text.
   * @param {string} [baseClass] - Optional class string (default: TAG_BASE_CLASS).
   * @returns {HTMLElement} Tag span with close button.
   */
  function createTag(text, baseClass) {
    const span = document.createElement('span');
    span.className = baseClass || TAG_BASE_CLASS;
    span.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-mint"></span> ${escapeHtml(text)} <button class="hover:text-white" type="button"><span class="material-symbols-outlined text-[14px]">close</span></button>`;
    const btn = span.querySelector('button');
    if (btn) btn.addEventListener('click', () => { span.remove(); });
    return span;
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  /**
   * Rebuild hidden task_N inputs in the contract form from current deliverable tags.
   * Only creates inputs for tags that have text — no empty slots.
   */
  function updateContractTasksFromList(listEl) {
    if (!listEl) return;
    var form = document.getElementById('post-contract-form');
    if (!form) return;
    form.querySelectorAll('input[name^="task_"]').forEach(function(el) { el.remove(); });
    var tags = Array.from(listEl.querySelectorAll('.tech-tag'));
    var idx = 1;
    tags.forEach(function(tag) {
      var text = getTagText(tag);
      if (!text) return;
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'task_' + idx;
      input.value = text;
      form.appendChild(input);
      idx++;
    });
  }

  /**
   * Get deliverable text from a tag (second text node, e.g. after bullet).
   * @param {HTMLElement} tag - .tech-tag element.
   * @returns {string}
   */
  function getTagText(tag) {
    return tag?.childNodes?.[1]?.textContent?.trim() ?? '';
  }

  /**
   * Bind deliverables input: add on button click and Enter, remove on tag close, sync contract tasks.
   */
  function bindDeliverables(el) {
    const { reqInput, reqAddBtn, reqList } = el;
    if (!reqAddBtn || !reqInput || !reqList) return;

    function addDeliverable() {
      const val = reqInput.value.trim();
      if (!val) return;
      reqList.appendChild(createTag(val));
      reqInput.value = '';
      updateContractTasksFromList(reqList);
    }

    reqAddBtn.addEventListener('click', (e) => {
      e.preventDefault();
      addDeliverable();
    });
    reqInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addDeliverable();
      }
    });

    reqList.addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (btn && btn.closest('span')) {
        btn.closest('span').remove();
        updateContractTasksFromList(reqList);
      }
    });

    updateContractTasksFromList(reqList);
  }

  /**
   * Bind technologies input: add on button and Enter; no contract sync.
   */
  function bindTechnologies(el) {
    const { techInput, techAddBtn, techList } = el;
    if (!techAddBtn || !techInput || !techList) return;

    function addTechnology() {
      const val = techInput.value.trim();
      if (!val) return;
      techList.appendChild(createTag(val, TAG_BASE_CLASS));
      techInput.value = '';
    }

    techAddBtn.addEventListener('click', (e) => {
      e.preventDefault();
      addTechnology();
    });
    techInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addTechnology();
      }
    });
  }

  /**
   * Update investment display (total £ and dev count label) from sliders.
   */
  function updateInvestmentDisplay(el) {
    const investEl = el.investmentAmount;
    if (!investEl) return;
    const devs = parseInt(el.devSlider?.value || DEFAULT_DEVS, 10);
    const perDev = parseInt(el.investmentPerDevSlider?.value || DEFAULT_PER_DEV, 10);
    investEl.textContent = `£${devs * perDev}`;
    if (el.devCount) {
      const devVal = el.devSlider?.value ?? DEFAULT_DEVS;
      el.devCount.innerHTML = `${devVal} <span class="text-xs uppercase text-slate-500">Devs</span>`;
    }
  }

  /**
   * Bind all sliders and keep displays in sync.
   */
  function bindSliders(el) {
    const {
      devSlider,
      devCount,
      timelineSlider,
      timelineDays,
      investmentPerDevSlider,
      investmentPerDevDisplay,
      minReqSlider,
      minReqDisplay,
    } = el;

    if (devSlider) {
      devSlider.addEventListener('input', () => updateInvestmentDisplay(el));
    }
    if (timelineSlider && timelineDays) {
      timelineSlider.addEventListener('input', () => {
        timelineDays.innerHTML = `${timelineSlider.value} <span class="text-xs uppercase text-slate-500">Days</span>`;
      });
    }
    if (investmentPerDevSlider && investmentPerDevDisplay) {
      investmentPerDevSlider.addEventListener('input', () => {
        investmentPerDevDisplay.innerHTML = `£${investmentPerDevSlider.value} <span class="text-xs uppercase text-slate-500">/ dev</span>`;
        updateInvestmentDisplay(el);
      });
    }
    if (minReqSlider && minReqDisplay) {
      minReqSlider.addEventListener('input', () => {
        minReqDisplay.innerHTML = `${minReqSlider.value} <span class="text-xs uppercase text-slate-500">tasks</span>`;
      });
    }

    updateInvestmentDisplay(el);
  }

  /**
   * Wire up all .js-help-toggle buttons to toggle their target panel.
   */
  function bindHelpToggles() {
    document.querySelectorAll('.js-help-toggle').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var targetId = this.getAttribute('data-target');
        var panel = targetId ? document.getElementById(targetId) : null;
        if (panel) panel.classList.toggle('hidden');
      });
    });
  }

  /**
   * Before launch form submit: sync hidden fields from contract form and sidebar sliders/tags.
   */
  function syncLaunchFormHiddenFields(el) {
    const company = el.postContractForm?.querySelector('input[name="company_name"]');
    const startDate = el.postContractForm?.querySelector('input[name="start_date"]');
    const endDate = el.postContractForm?.querySelector('input[name="end_date"]');

    const setLaunch = (id, value) => {
      const field = document.getElementById(id);
      if (field) field.value = value;
    };

    setLaunch('launch-company_name', company?.value ?? '');
    setLaunch('launch-sprint_begins_at', startDate?.value ?? '');
    setLaunch('launch-sprint_ends_at', endDate?.value ?? '');
    setLaunch('launch-signup_ends_at', startDate?.value ?? '');
    setLaunch('launch-max_talent_pool', el.devSlider?.value ?? DEFAULT_DEVS);

    const perDev = parseInt(el.investmentPerDevSlider?.value || DEFAULT_PER_DEV, 10);
    setLaunch('launch-pay_for_prototype', String(perDev));
    setLaunch('launch-sprint_timeline_days', el.timelineSlider?.value ?? DEFAULT_TIMELINE_DAYS);
    setLaunch('launch-minimum_requirements_for_pay', el.minReqSlider?.value ?? DEFAULT_MIN_REQUIREMENTS);

    const techTags = el.techList
      ? Array.from(el.techList.querySelectorAll('.tech-tag')).map(getTagText).filter(Boolean)
      : [];
    setLaunch('launch-technologies_required', techTags.join(', '));

    const deliverableTags = el.reqList
      ? Array.from(el.reqList.querySelectorAll('.tech-tag')).map(getTagText).filter(Boolean)
      : [];
    setLaunch('launch-deliverables', deliverableTags.join('\n'));
  }

  /**
   * Bind launch form submit to sync hidden fields then allow default submit.
   */
  function bindLaunchForm(el) {
    if (!el.launchForm) return;
    el.launchForm.addEventListener('submit', () => syncLaunchFormHiddenFields(el));
  }

  /**
   * Initialize dashboard: bind all behaviors.
   */
  function init() {
    const el = getDOMElements();
    bindDeliverables(el);
    bindTechnologies(el);
    bindSliders(el);
    bindHelpToggles();
    bindLaunchForm(el);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
