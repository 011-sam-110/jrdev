// developer_dashboard.js – toggles for Edit Markdown and Add Project

document.addEventListener('DOMContentLoaded', function() {
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
});
