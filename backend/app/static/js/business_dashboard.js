/**
 * Business Dashboard – modular UI logic (deliverables, technologies, sliders, launch form).
 * Preserves all existing behavior; no features removed.
 */

(function () {
  'use strict';

  function showFormError(form, message) {
    var existing = form.querySelector('.js-form-error');
    if (existing) existing.remove();
    var el = document.createElement('div');
    el.className = 'js-form-error rounded-lg px-4 py-3 text-sm font-medium bg-red-500/15 border border-red-500/30 text-red-300 mb-4';
    el.setAttribute('role', 'alert');
    el.textContent = message;
    form.prepend(el);
    setTimeout(function() { el.remove(); }, 5000);
  }

  const DEFAULT_DEVS = 3;
  const DEFAULT_PER_DEV = 50;
  const MIN_PER_DEV = 50;
  const MAX_PER_DEV = 300;
  const DEFAULT_TIMELINE_DAYS = 7;
  const DEFAULT_MIN_REQUIREMENTS = 1;

  const TAG_BASE_CLASS = 'tech-tag flex items-center gap-2 px-3 py-1.5 bg-navy-700/50 border border-white/10 rounded-lg text-xs font-medium text-slate-300';
  const ESSENTIAL_TAG_CLASS = 'tech-tag flex items-center gap-2 px-3 py-1.5 bg-navy-700/50 border border-amber-500/30 rounded-lg text-xs font-medium text-slate-300';

  /**
   * Resolve all dashboard DOM elements once.
   * @returns {Object} Refs to inputs, lists, sliders, forms.
   */
  function getDOMElements() {
    const reqInput = document.getElementById('requirement-buffet-input');
    const techInput = document.getElementById('technologies-required-input');
    const techList = document.getElementById('technologies-tags-list');
    const devSlider = document.querySelector('.dev-allocation-slider') || document.querySelector('input[type="range"][max="5"]');
    const investmentPerDevSlider = document.querySelector('.investment-per-dev-slider');
    const minReqSlider = document.querySelector('.min-requirements-slider');
    const essentialSlider = document.querySelector('.essential-deliverables-slider');
    const postContractForm = document.getElementById('post-contract-form');
    const launchForm = document.getElementById('launch-sprint-form');

    return {
      reqInput,
      reqAddBtn: reqInput?.parentElement?.querySelector('button'),
      reqList: document.getElementById('requirement-buffet-list'),
      essentialInput: document.getElementById('essential-deliverables-input'),
      essentialAddBtn: document.getElementById('essential-deliverables-add-btn'),
      essentialList: document.getElementById('essential-deliverables-list'),
      essentialCapNum: document.querySelector('.essential-deliverables-cap-num'),
      deliverablesCapNum: document.querySelector('.deliverables-cap-num'),
      techInput,
      techAddBtn: document.getElementById('technologies-add-btn'),
      techList,
      devSlider,
      devCount: document.querySelector('.dev-count'),
      devCountValue: document.querySelector('.dev-count-value'),
      investmentPerDevSlider,
      investmentPerDevDisplay: document.querySelector('.investment-per-dev'),
      investmentPerDevValue: document.querySelector('.investment-per-dev-value'),
      minReqSlider,
      minReqDisplay: document.querySelector('.min-requirements-display'),
      minRequirementsValue: document.querySelector('.min-requirements-value'),
      minRequirementsLabel: document.querySelector('.min-requirements-label'),
      essentialSlider,
      essentialDisplay: document.querySelector('.essential-deliverables-display'),
      essentialDeliverablesValue: document.querySelector('.essential-deliverables-value'),
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
  function createTag(text, baseClass, dotClass) {
    const span = document.createElement('span');
    span.className = baseClass || TAG_BASE_CLASS;
    const dot = 'w-1.5 h-1.5 rounded-full ' + (dotClass || 'bg-mint');
    span.innerHTML = `<span class="${dot}"></span> ${escapeHtml(text)} <button class="hover:text-white" type="button"><span class="material-symbols-outlined text-[14px]">close</span></button>`;
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
   * Rebuild hidden task_N inputs from essential list + optional list (in that order).
   */
  function updateContractTasksFromDeliverables(essentialListEl, optionalListEl) {
    var form = document.getElementById('post-contract-form');
    if (!form) return;
    form.querySelectorAll('input[name^="task_"]').forEach(function(el) { el.remove(); });
    var tasks = [];
    if (essentialListEl) {
      tasks = tasks.concat(Array.from(essentialListEl.querySelectorAll('.tech-tag')).map(getTagText).filter(Boolean));
    }
    if (optionalListEl) {
      tasks = tasks.concat(Array.from(optionalListEl.querySelectorAll('.tech-tag')).map(getTagText).filter(Boolean));
    }
    tasks.forEach(function(text, i) {
      var input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'task_' + (i + 1);
      input.value = text;
      form.appendChild(input);
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

  /** Essential max = half of min deliverables for pay (total deliverables / 2). */
  function getEssentialMax(el) {
    const minReq = parseInt(el.minReqSlider?.value || DEFAULT_MIN_REQUIREMENTS, 10);
    return Math.floor(minReq / 2);
  }

  function getEssentialCap(el) {
    const maxVal = getEssentialMax(el);
    const raw = parseInt(el.essentialSlider?.value || 0, 10);
    return Math.min(Math.max(0, raw), maxVal);
  }

  function getOptionalCap(el) {
    const minReq = parseInt(el.minReqSlider?.value || DEFAULT_MIN_REQUIREMENTS, 10);
    const essential = getEssentialCap(el);
    return Math.max(0, minReq - essential);
  }

  function updateCapHints(el) {
    const optionalCap = getOptionalCap(el);
    const essentialCap = getEssentialCap(el);
    if (el.deliverablesCapNum) el.deliverablesCapNum.textContent = String(optionalCap);
    if (el.essentialCapNum) el.essentialCapNum.textContent = String(essentialCap);
  }

  function updateEssentialMaxLabel(el) {
    const label = document.querySelector('.essential-deliverables-max-label');
    if (label) label.textContent = String(getEssentialMax(el));
  }

  function syncContractTasks(el) {
    updateContractTasksFromDeliverables(el.essentialList, el.reqList);
  }

  /**
   * Sync post-contract form hidden fields (pay, min_tasks, essential_count) from sidebar. Call before Generate PDF submit.
   */
  function syncPostContractForm(el) {
    var form = document.getElementById('post-contract-form');
    if (!form) return;
    syncContractTasks(el);
    var payEl = document.getElementById('post-contract-pay');
    var minTasksEl = document.getElementById('post-contract-min_tasks');
    var essentialEl = document.getElementById('post-contract-essential_count');
    if (payEl) payEl.value = el.investmentPerDevSlider?.value ?? DEFAULT_PER_DEV;
    if (minTasksEl) minTasksEl.value = el.minReqSlider?.value ?? DEFAULT_MIN_REQUIREMENTS;
    if (essentialEl) {
      var count = el.essentialList ? el.essentialList.querySelectorAll('.tech-tag').length : 0;
      essentialEl.value = String(count);
    }
  }

  /**
   * Bind optional deliverables: add only up to (minReq - essential); sync contract tasks.
   */
  function bindDeliverables(el) {
    const { reqInput, reqAddBtn, reqList } = el;
    if (!reqAddBtn || !reqInput || !reqList) return;

    function optionalCount() {
      return el.reqList ? el.reqList.querySelectorAll('.tech-tag').length : 0;
    }

    function addDeliverable() {
      const val = reqInput.value.trim();
      if (!val) return;
      const cap = getOptionalCap(el);
      if (optionalCount() >= cap) return;
      reqList.appendChild(createTag(val));
      reqInput.value = '';
      syncContractTasks(el);
      updateCapHints(el);
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
        syncContractTasks(el);
        updateCapHints(el);
      }
    });

    syncContractTasks(el);
    updateCapHints(el);
  }

  /**
   * Bind essential deliverables: add only up to essential slider value.
   */
  function bindEssentialDeliverables(el) {
    const { essentialInput, essentialAddBtn, essentialList } = el;
    if (!essentialInput || !essentialAddBtn || !essentialList) return;

    function essentialCount() {
      return el.essentialList ? el.essentialList.querySelectorAll('.tech-tag').length : 0;
    }

    function addEssential() {
      const val = essentialInput.value.trim();
      if (!val) return;
      const cap = getEssentialCap(el);
      if (essentialCount() >= cap) return;
      essentialList.appendChild(createTag(val, ESSENTIAL_TAG_CLASS, 'bg-amber-400'));
      essentialInput.value = '';
      syncContractTasks(el);
      updateCapHints(el);
    }

    essentialAddBtn.addEventListener('click', (e) => {
      e.preventDefault();
      addEssential();
    });
    essentialInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        addEssential();
      }
    });

    essentialList.addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (btn && btn.closest('span')) {
        btn.closest('span').remove();
        syncContractTasks(el);
        updateCapHints(el);
      }
    });

    syncContractTasks(el);
    updateCapHints(el);
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
    investEl.textContent = '£' + (devs * perDev);
    if (el.devCountValue) el.devCountValue.textContent = String(devs);
    if (el.investmentPerDevValue) el.investmentPerDevValue.textContent = String(perDev);
    var minVal = el.minReqSlider?.value ?? DEFAULT_MIN_REQUIREMENTS;
    if (el.minRequirementsValue) el.minRequirementsValue.textContent = String(minVal);
    if (el.minRequirementsLabel) el.minRequirementsLabel.textContent = parseInt(minVal, 10) === 1 ? 'task' : 'tasks';
    var essVal = el.essentialSlider ? Math.min(parseInt(el.essentialSlider.value, 10), getEssentialMax(el)) : 0;
    if (el.essentialDeliverablesValue) el.essentialDeliverablesValue.textContent = String(essVal);
  }

  /**
   * Bind all sliders and keep displays in sync. Essential slider max = minReq; cap hints updated.
   */
  function bindSliders(el) {
    const {
      devSlider,
      devCount,
      investmentPerDevSlider,
      investmentPerDevDisplay,
      minReqSlider,
      minReqDisplay,
      essentialSlider,
      essentialDisplay,
    } = el;

    function clampEssentialToMinReq() {
      if (!essentialSlider || !minReqSlider) return;
      const maxVal = getEssentialMax(el);
      essentialSlider.setAttribute('max', String(maxVal));
      const current = parseInt(essentialSlider.value, 10);
      if (current > maxVal) {
        essentialSlider.value = String(maxVal);
        if (essentialDisplay) essentialDisplay.innerHTML = `${maxVal} <span class="text-xs uppercase text-slate-500">required</span>`;
      }
      updateEssentialMaxLabel(el);
      updateCapHints(el);
    }

    function clampPerDev(val) { return Math.min(MAX_PER_DEV, Math.max(MIN_PER_DEV, parseInt(val, 10) || DEFAULT_PER_DEV)); }

    if (devSlider) {
      devSlider.addEventListener('input', () => updateInvestmentDisplay(el));
    }
    if (investmentPerDevSlider) {
      investmentPerDevSlider.addEventListener('input', () => {
        var v = clampPerDev(investmentPerDevSlider.value);
        investmentPerDevSlider.value = String(v);
        updateInvestmentDisplay(el);
      });
    }
    if (minReqSlider && minReqDisplay) {
      minReqSlider.addEventListener('input', () => {
        clampEssentialToMinReq();
        updateInvestmentDisplay(el);
      });
    }
    if (essentialSlider && essentialDisplay) {
      essentialSlider.addEventListener('input', () => {
        const maxVal = getEssentialMax(el);
        const val = Math.min(Math.max(0, parseInt(essentialSlider.value, 10)), maxVal);
        essentialSlider.value = String(val);
        updateEssentialMaxLabel(el);
        updateCapHints(el);
        updateInvestmentDisplay(el);
      });
    }

    updateInvestmentDisplay(el);
    clampEssentialToMinReq();
  }

  /**
   * Initialize Flatpickr date pickers (Material/Calendar-inspired).
   */
  function bindDatePickers() {
    const startEl = document.getElementById('sprint-start-date');
    const endEl = document.getElementById('sprint-end-date');
    if (!startEl || !endEl || typeof flatpickr === 'undefined') return;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const startFp = flatpickr(startEl, {
      dateFormat: 'Y-m-d',
      minDate: today,
      allowInput: true,
      theme: 'dark',
      onChange: function(selectedDates) {
        if (selectedDates[0]) {
          const start = selectedDates[0];
          const minEnd = new Date(start);
          minEnd.setDate(minEnd.getDate() + 3);
          const maxEnd = new Date(start);
          maxEnd.setDate(maxEnd.getDate() + 14);
          endFp.set('minDate', minEnd);
          endFp.set('maxDate', maxEnd);
          if (endFp.selectedDates[0]) {
            const end = endFp.selectedDates[0];
            const days = Math.round((end - start) / (24 * 60 * 60 * 1000));
            if (days < 3 || days > 14) endFp.clear();
          }
        }
      }
    });

    const endFp = flatpickr(endEl, {
      dateFormat: 'Y-m-d',
      minDate: today,
      allowInput: true,
      theme: 'dark',
      onChange: function() {}
    });
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
    const companyAddr = el.postContractForm?.querySelector('input[name="company_address"]');
    const startDate = el.postContractForm?.querySelector('input[name="start_date"]');
    const endDate = el.postContractForm?.querySelector('input[name="end_date"]');

    const setLaunch = (id, value) => {
      const field = document.getElementById(id);
      if (field) field.value = value;
    };

    setLaunch('launch-company_name', company?.value ?? '');
    setLaunch('launch-company_address', companyAddr?.value ?? '');
    setLaunch('launch-sprint_begins_at', startDate?.value ?? '');
    setLaunch('launch-sprint_ends_at', endDate?.value ?? '');
    setLaunch('launch-signup_ends_at', startDate?.value ?? '');
    setLaunch('launch-max_talent_pool', el.devSlider?.value ?? DEFAULT_DEVS);

    const perDev = parseInt(el.investmentPerDevSlider?.value || DEFAULT_PER_DEV, 10);
    setLaunch('launch-pay_for_prototype', String(perDev));
    setLaunch('launch-minimum_requirements_for_pay', el.minReqSlider?.value ?? DEFAULT_MIN_REQUIREMENTS);
    setLaunch('launch-essential_deliverables_count', el.essentialSlider?.value ?? '0');
    const essentialTags = el.essentialList
      ? Array.from(el.essentialList.querySelectorAll('.tech-tag')).map(getTagText).filter(Boolean)
      : [];
    setLaunch('launch-essential_deliverables', essentialTags.join('\n'));

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
   * Before post-contract form submit: sync pay, min_tasks, essential_count from sidebar.
   */
  function syncPostContractForm(el) {
    var form = el.postContractForm;
    if (!form) return;
    syncContractTasks(el);
    var payEl = document.getElementById('post-contract-pay');
    var minEl = document.getElementById('post-contract-min_tasks');
    var essentialEl = document.getElementById('post-contract-essential_count');
    if (payEl) payEl.value = el.investmentPerDevSlider?.value ?? DEFAULT_PER_DEV;
    if (minEl) minEl.value = el.minReqSlider?.value ?? DEFAULT_MIN_REQUIREMENTS;
    if (essentialEl) {
      var count = el.essentialList ? el.essentialList.querySelectorAll('.tech-tag').length : 0;
      essentialEl.value = String(count);
    }
  }

  /**
   * Bind post-contract form submit: sync hidden fields before submit.
   */
  function bindPostContractForm(el) {
    if (!el.postContractForm) return;
    el.postContractForm.addEventListener('submit', function() {
      syncPostContractForm(el);
    });
  }

  /**
   * Bind launch form submit: validate technologies + card, sync hidden fields, then allow default submit.
   */
  function bindLaunchForm(el) {
    if (!el.launchForm) return;
    el.launchForm.addEventListener('submit', function(ev) {
      var hasCard = el.launchForm.getAttribute('data-has-card') === 'true';
      var billingUrl = el.launchForm.getAttribute('data-billing-url') || '';
      if (!hasCard && billingUrl) {
        ev.preventDefault();
        window.location.href = billingUrl;
        return;
      }
      var techTags = el.techList ? Array.from(el.techList.querySelectorAll('.tech-tag')).map(getTagText).filter(Boolean) : [];
      if (techTags.length === 0) {
        ev.preventDefault();
        showFormError(el.launchForm, 'Please add at least one technology before launching a sprint.');
        return;
      }
      syncLaunchFormHiddenFields(el);
      var startVal = el.launchForm.querySelector('#launch-sprint_begins_at')?.value;
      var endVal = el.launchForm.querySelector('#launch-sprint_ends_at')?.value;
      if (startVal && endVal) {
        var start = new Date(startVal);
        var end = new Date(endVal);
        var days = Math.round((end - start) / (1000 * 60 * 60 * 24));
        if (days < 3) {
          ev.preventDefault();
          showFormError(el.launchForm, 'Sprint duration must be at least 3 days.');
          return;
        }
        if (days > 14) {
          ev.preventDefault();
          showFormError(el.launchForm, 'Sprint duration cannot exceed 14 days (2 weeks).');
          return;
        }
      }
    });
  }

  /**
   * Initialize dashboard: bind all behaviors.
   */
  function init() {
    const el = getDOMElements();
    bindSliders(el);
    bindDeliverables(el);
    bindEssentialDeliverables(el);
    bindTechnologies(el);
    bindDatePickers();
    bindHelpToggles();
    bindLaunchForm(el);
    bindPostContractForm(el);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
