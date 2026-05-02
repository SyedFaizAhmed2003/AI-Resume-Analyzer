document.addEventListener('DOMContentLoaded', () => {
    // ---- Sidebar Navigation ----
    const navLinks = document.querySelectorAll('.nav-links li');
    const views = document.querySelectorAll('.view');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Show corresponding view
            const targetId = link.getAttribute('data-target');
            views.forEach(view => {
                if(view.id === targetId) {
                    view.classList.remove('hidden');
                    view.classList.add('active');
                } else {
                    view.classList.add('hidden');
                    view.classList.remove('active');
                }
            });
            
            if(targetId === 'view-feedback') fetchPublicFeedback();
        });
    });

    // ---- Theme Toggle ----
    const themeBtn = document.getElementById('theme-toggle-btn');
    const themeLabel = document.getElementById('theme-label');
    themeBtn.addEventListener('change', () => {
        if(themeBtn.checked) {
            document.body.classList.add('light-theme');
            themeLabel.textContent = 'Light Mode';
        } else {
            document.body.classList.remove('light-theme');
            themeLabel.textContent = 'Dark Mode';
        }
        
        // Redraw charts with correct text colors
        if (cachedAdminUserData && cachedAdminUserData.length) drawAdminCharts(cachedAdminUserData);
        if (publicChartInstance) fetchPublicFeedback();
    });

    // ---- Analyzer View Logic ----
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const uploadSection = document.getElementById('upload-section');
    const loadingState = document.getElementById('loading');
    const dashboard = document.getElementById('dashboard');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');

    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault(); dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    
    // Allow clicking anywhere in the drop zone to open file picker
    dropZone.addEventListener('click', (e) => {
        // Prevent double trigger if they click the button itself
        if (e.target !== browseBtn) {
            fileInput.click();
        }
    });

    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => { if (e.target.files.length) handleFile(e.target.files[0]); });
    newAnalysisBtn.addEventListener('click', () => {
        dashboard.classList.add('hidden');
        dropZone.classList.remove('hidden');
        fileInput.value = '';
    });

    function handleFile(file) {
        if (file.type !== 'application/pdf') { alert('Please upload a PDF file.'); return; }
        uploadFile(file);
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        dropZone.classList.add('hidden');
        loadingState.classList.remove('hidden');

        try {
            const response = await fetch('http://localhost:8000/api/analyze', { method: 'POST', body: formData });
            if (!response.ok) throw new Error('Analysis failed. Make sure backend is running.');
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            populateDashboard(data);
            loadingState.classList.add('hidden');
            dashboard.classList.remove('hidden');
        } catch (error) {
            alert(error.message || 'An error occurred.');
            loadingState.classList.add('hidden');
            dropZone.classList.remove('hidden');
        }
    }

    function populateDashboard(data) {
        document.getElementById('res-name').textContent = data.basic_info.name || 'N/A';
        document.getElementById('res-email').textContent = data.basic_info.email || 'N/A';
        document.getElementById('res-mobile').textContent = data.basic_info.mobile_number || 'N/A';
        document.getElementById('res-pages').textContent = data.basic_info.no_of_pages || 'N/A';
        document.getElementById('res-level').textContent = data.cand_level || 'N/A';

        const score = data.resume_score || 0;
        document.getElementById('res-score').textContent = score;
        document.getElementById('score-circle-path').setAttribute('stroke-dasharray', `${score}, 100`);
        const circlePath = document.getElementById('score-circle-path');
        if(score > 75) circlePath.style.stroke = '#00ffcc';
        else if(score > 40) circlePath.style.stroke = '#ffcc00';
        else circlePath.style.stroke = '#ff3366';

        document.getElementById('res-field').textContent = data.reco_field || 'General / N/A';

        const currentSkills = document.getElementById('current-skills');
        currentSkills.innerHTML = data.skills?.length ? data.skills.map(s => `<span class="tag">${s}</span>`).join('') : '<span class="tag">None extracted</span>';

        const recSkills = document.getElementById('recommended-skills');
        recSkills.innerHTML = data.recommended_skills?.length ? data.recommended_skills.map(s => `<span class="tag">${s}</span>`).join('') : '<span class="tag">No specific recommendations</span>';

        const courseList = document.getElementById('course-list');
        courseList.innerHTML = data.courses?.length ? data.courses.map(c => `<li class="course-item"><a href="${c.link}" target="_blank">${c.name}</a></li>`).join('') : '<li>No specific courses.</li>';

        // Videos
        const vidContainer = document.getElementById('video-container');
        if(data.resume_video || data.interview_video) {
            vidContainer.classList.remove('hidden');
            const resVid = document.getElementById('vid-resume');
            const intVid = document.getElementById('vid-interview');
            
            function getYoutubeEmbedUrl(url) {
                if (!url) return '';
                let videoId = '';
                if (url.includes('youtu.be/')) videoId = url.split('youtu.be/')[1].split('?')[0];
                else if (url.includes('watch?v=')) videoId = url.split('watch?v=')[1].split('&')[0];
                return videoId ? `https://www.youtube.com/embed/${videoId}` : url;
            }
            
            if(data.resume_video) resVid.src = getYoutubeEmbedUrl(data.resume_video);
            if(data.interview_video) intVid.src = getYoutubeEmbedUrl(data.interview_video);
        } else {
            vidContainer.classList.add('hidden');
        }
    }

    // ---- Feedback View Logic ----
    const feedbackForm = document.getElementById('feedback-form');
    feedbackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const payload = {
            name: document.getElementById('feed-name').value,
            email: document.getElementById('feed-email').value,
            score: document.getElementById('feed-score').value,
            comments: document.getElementById('feed-comments').value
        };

        try {
            const res = await fetch('http://localhost:8000/api/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if(res.ok) {
                alert("Thanks! Your feedback was recorded.");
                feedbackForm.reset();
                fetchPublicFeedback();
            }
        } catch(err) {
            console.error(err);
        }
    });

    let publicChartInstance = null;
    async function fetchPublicFeedback() {
        try {
            const res = await fetch('http://localhost:8000/api/admin/data');
            const data = await res.json();
            if(data.success) {
                const ratings = {1:0, 2:0, 3:0, 4:0, 5:0};
                data.feedback_data.forEach(f => {
                    const sc = parseInt(f.feed_score);
                    if(ratings[sc] !== undefined) ratings[sc]++;
                });

                const isLight = document.body.classList.contains('light-theme');
                const textColor = isLight ? '#1a1a24' : '#f0f0f0';
                const ctx = document.getElementById('public-ratings-chart').getContext('2d');
                if(publicChartInstance) publicChartInstance.destroy();
                publicChartInstance = new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
                        datasets: [{
                            data: [ratings[1], ratings[2], ratings[3], ratings[4], ratings[5]],
                            backgroundColor: ['#f43f5e', '#f59e0b', '#eab308', '#06b6d4', '#6366f1'],
                            borderWidth: 0
                        }]
                    },
                    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: textColor } } } }
                });
            }
        } catch(e) { console.error(e); }
    }

    // ---- Admin Dashboard Logic ----
    const adminLoginForm = document.getElementById('admin-login-form');
    const adminLoginSection = document.getElementById('admin-login-section');
    const adminDashboardSection = document.getElementById('admin-dashboard-section');
    const adminError = document.getElementById('admin-error');
    
    let adminCharts = []; // store instances to destroy on refresh

    adminLoginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const user = document.getElementById('admin-user').value;
        const pass = document.getElementById('admin-pass').value;

        try {
            const res = await fetch('http://localhost:8000/api/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({username: user, password: pass})
            });
            const data = await res.json();
            if(data.success) {
                adminLoginSection.classList.add('hidden');
                adminDashboardSection.classList.remove('hidden');
                fetchAdminData();
            } else {
                adminError.classList.remove('hidden');
            }
        } catch(err) {
            console.error(err);
        }
    });

    let cachedAdminUserData = [];

    async function fetchAdminData() {
        try {
            const res = await fetch('http://localhost:8000/api/admin/data');
            const data = await res.json();
            if(data.success) {
                cachedAdminUserData = data.user_data;
                document.getElementById('admin-welcome').textContent = `Welcome Admin! Total Users: ${data.user_data.length}`;
                
                populateAdminTables(data.user_data, data.feedback_data);
                drawAdminCharts(data.user_data);
            }
        } catch(e) { console.error(e); }
    }

    function populateAdminTables(userData, feedData) {
        const uTbody = document.querySelector('#admin-user-table tbody');
        uTbody.innerHTML = userData.map(u => `
            <tr>
                <td>${u.ID}</td>
                <td>${u.Timestamp}</td>
                <td>${u.Name}</td>
                <td>${u.Email_ID}</td>
                <td>${u.resume_score}</td>
                <td>${u.User_level}</td>
                <td>${u.Predicted_Field}</td>
                <td>${u.city}, ${u.country}</td>
            </tr>
        `).join('');

        const fTbody = document.querySelector('#admin-feed-table tbody');
        fTbody.innerHTML = feedData.map(f => `
            <tr>
                <td>${f.ID}</td>
                <td>${f.Timestamp}</td>
                <td>${f.feed_name}</td>
                <td>${f.feed_score}/5</td>
                <td>${f.comments}</td>
            </tr>
        `).join('');
    }

    function drawAdminCharts(users) {
        adminCharts.forEach(c => c.destroy());
        adminCharts = [];

        const isLight = document.body.classList.contains('light-theme');
        const textColor = isLight ? '#1a1a24' : '#f0f0f0';
        const titleColor = isLight ? '#1a1a24' : '#fff';

        // Setup common chart config
        const commonOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: textColor } } } };
        const colors = ['#6366f1', '#06b6d4', '#8b5cf6', '#ec4899', '#f59e0b'];

        // Roles
        const roleCounts = {};
        users.forEach(u => { roleCounts[u.Predicted_Field] = (roleCounts[u.Predicted_Field] || 0) + 1; });
        adminCharts.push(new Chart(document.getElementById('chart-roles'), {
            type: 'pie', data: { labels: Object.keys(roleCounts), datasets: [{ data: Object.values(roleCounts), backgroundColor: colors }] },
            options: { ...commonOptions, plugins: { ...commonOptions.plugins, title: { display: true, text: 'Predicted Roles', color: titleColor } } }
        }));

        // Experience
        const expCounts = {};
        users.forEach(u => { expCounts[u.User_level] = (expCounts[u.User_level] || 0) + 1; });
        adminCharts.push(new Chart(document.getElementById('chart-experience'), {
            type: 'pie', data: { labels: Object.keys(expCounts), datasets: [{ data: Object.values(expCounts), backgroundColor: colors }] },
            options: { ...commonOptions, plugins: { ...commonOptions.plugins, title: { display: true, text: 'Experience Levels', color: titleColor } } }
        }));

        // Geo
        const geoCounts = {};
        users.forEach(u => { const loc = `${u.city}, ${u.country}`; geoCounts[loc] = (geoCounts[loc] || 0) + 1; });
        adminCharts.push(new Chart(document.getElementById('chart-geo'), {
            type: 'doughnut', data: { labels: Object.keys(geoCounts), datasets: [{ data: Object.values(geoCounts), backgroundColor: colors }] },
            options: { ...commonOptions, plugins: { ...commonOptions.plugins, title: { display: true, text: 'Geography', color: titleColor } } }
        }));

        // Scores
        const scoreCounts = {};
        users.forEach(u => { scoreCounts[u.resume_score] = (scoreCounts[u.resume_score] || 0) + 1; });
        adminCharts.push(new Chart(document.getElementById('chart-scores'), {
            type: 'pie', data: { labels: Object.keys(scoreCounts), datasets: [{ data: Object.values(scoreCounts), backgroundColor: colors }] },
            options: { ...commonOptions, plugins: { ...commonOptions.plugins, title: { display: true, text: 'Resume Scores', color: titleColor } } }
        }));
    }

    // CSV Download
    document.getElementById('download-csv-btn').addEventListener('click', () => {
        if(!cachedAdminUserData.length) return alert('No data to export.');
        
        const headers = Object.keys(cachedAdminUserData[0]).join(',');
        const rows = cachedAdminUserData.map(obj => Object.values(obj).map(val => `"${val}"`).join(',')).join('\n');
        const csvContent = headers + '\n' + rows;
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", "User_Data_Report.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
});
