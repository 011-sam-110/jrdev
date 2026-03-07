/**
 * developer_dashboard.js
 * Toggles for Edit Markdown and Add Pinned Project on the developer dashboard.
 * No build step; loaded by developer_dashboard.html.
 */
document.addEventListener('DOMContentLoaded', function() {
    // ---- Edit Markdown toggle ----
    var toggleMd = document.getElementById('toggle-markdown-edit');
    var cancelMd = document.getElementById('cancel-markdown-edit');
    var markdownView = document.getElementById('markdown-view');
    var markdownEdit = document.getElementById('markdown-edit');

    if (toggleMd && markdownView && markdownEdit) {
        toggleMd.addEventListener('click', function() {
            markdownView.classList.add('hidden');
            markdownEdit.classList.remove('hidden');
        });
    }
    if (cancelMd && markdownView && markdownEdit) {
        cancelMd.addEventListener('click', function() {
            markdownView.classList.remove('hidden');
            markdownEdit.classList.add('hidden');
        });
    }

    // ---- About Me character count ----
    var aboutMeTextarea = document.getElementById('about-me-textarea');
    var aboutMeCount = document.getElementById('about-me-count');
    if (aboutMeTextarea && aboutMeCount) {
        aboutMeTextarea.addEventListener('input', function() {
            aboutMeCount.textContent = this.value.length;
        });
    }

    // ---- Add Pinned Project toggle ----
    var toggleProject = document.getElementById('toggle-add-project');
    var cancelProject = document.getElementById('cancel-add-project');
    var addProjectForm = document.getElementById('add-project-form');

    if (toggleProject && addProjectForm) {
        toggleProject.addEventListener('click', function() {
            addProjectForm.classList.toggle('hidden');
        });
    }
    if (cancelProject && addProjectForm) {
        cancelProject.addEventListener('click', function() {
            addProjectForm.classList.add('hidden');
        });
    }
    document.querySelectorAll('.js-open-add-project').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (addProjectForm) {
                addProjectForm.classList.remove('hidden');
                addProjectForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    var sidebarToggle = document.getElementById('dashboard-sidebar-toggle');
    var sidebarContent = document.getElementById('dashboard-sidebar-content');
    var sidebarLabel = document.getElementById('dashboard-sidebar-toggle-label');
    if (sidebarToggle && sidebarContent) {
        sidebarToggle.addEventListener('click', function() {
            var isHidden = sidebarContent.classList.contains('hidden');
            sidebarContent.classList.toggle('hidden');
            sidebarContent.classList.toggle('block', !isHidden);
            sidebarContent.setAttribute('aria-hidden', isHidden ? 'false' : 'true');
            sidebarToggle.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
            if (sidebarLabel) {
                sidebarLabel.textContent = isHidden ? 'Hide profile & stats' : 'Show profile & stats';
            }
        });
    }
});
