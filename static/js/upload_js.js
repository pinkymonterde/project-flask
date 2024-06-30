document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const descriptionInput = document.getElementById('descriptionInput');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('description', descriptionInput.value);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadFiles();
        } else {
            alert('File upload failed.');
        }
    })
    .catch(error => console.error('Error:', error));
});

function loadFiles() {
    fetch('/files')
        .then(response => response.json())
        .then(data => {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            data.files.forEach(file => {
                const listItem = document.createElement('div');
                listItem.textContent = `${file.name} - ${file.description}`;
                fileList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error:', error));
}

document.addEventListener('DOMContentLoaded', loadFiles);
