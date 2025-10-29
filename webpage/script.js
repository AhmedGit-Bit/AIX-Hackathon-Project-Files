
// ============================================
// DATA MANAGEMENT
// ============================================
let investments = [
    {
        id: 1,
        company: "TechVision AI",
        industry: "Technology",
        fundingRound: "Series A",
        amount: "$2,500,000",
        iaiScore: 85,
        status: "Excellent",
        lastUpdated: "Oct 20, 2025"
    },
    {
        id: 2,
        company: "HealthTech Solutions",
        industry: "Healthcare",
        fundingRound: "Series B",
        amount: "$5,000,000",
        iaiScore: 78,
        status: "Good",
        lastUpdated: "Oct 18, 2025"
    },
    {
        id: 3,
        company: "GreenEnergy Corp",
        industry: "Energy",
        fundingRound: "Seed",
        amount: "$750,000",
        iaiScore: 92,
        status: "Excellent",
        lastUpdated: "Oct 22, 2025"
    }
];

        let currentSort = { column: null, ascending: true };

        // ============================================
        // NAVIGATION
        // ============================================
document.querySelectorAll('.nav-link[data-page]').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const page = this.dataset.page;
        showPage(page);

        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
    });
});

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => page.classList.add('hidden'));
    document.getElementById(pageName + '-page').classList.remove('hidden');

    if (pageName === 'dashboard') {
        renderDashboardTable();
    }
}

// ============================================
// RENDER DASHBOARD TABLE
// ============================================
function renderDashboardTable() {
    const tbody = document.getElementById('investmentTableBody');
    tbody.innerHTML = '';

    investments.forEach(inv => {
        const row = tbody.insertRow();

        row.innerHTML = `
            <td><strong>${inv.company}</strong></td>
            <td>${inv.industry}</td>
            <td>${inv.fundingRound}</td>
            <td>${inv.amount}</td>
            <td>
                <div class="iai-score">
                    <span style="color: ${getScoreColor(inv.iaiScore)}">${inv.iaiScore}</span>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${inv.iaiScore}%; background: ${getScoreColor(inv.iaiScore)};"></div>
                    </div>
                </div>
            </td>
            <td><span class="status-badge ${getStatusClass(inv.status)}">${inv.status}</span></td>
            <td>${inv.lastUpdated}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-secondary" onclick="editInvestment(${inv.id})">Edit</button>
                    <button class="btn btn-danger" onclick="deleteInvestment(${inv.id})">Delete</button>
                </div>
            </td>
        `;
    });
}

        // ============================================
        // SEARCH/FILTER
        // ============================================
        function filterDashboardTable() {
            const input = document.getElementById('dashboardSearch').value.toLowerCase();
            const tbody = document.getElementById('investmentTableBody');
            const rows = tbody.getElementsByTagName('tr');

            for (let row of rows) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(input) ? '' : 'none';
            }
        }

        // ============================================
        // SORTING
        // ============================================
        function sortTable(column) {
            // Toggle sort direction
            if (currentSort.column === column) {
                currentSort.ascending = !currentSort.ascending;
            } else {
                currentSort.column = column;
                currentSort.ascending = true;
            }

            // Sort investments array
            investments.sort((a, b) => {
                let aVal = a[column];
                let bVal = b[column];

                // Handle numeric comparisons
                if (column === 'iaiScore') {
                    aVal = parseInt(aVal);
                    bVal = parseInt(bVal);
                }

                // Handle amount comparisons (remove $ and commas)
                if (column === 'amount') {
                    aVal = parseInt(aVal.replace(/[$,]/g, ''));
                    bVal = parseInt(bVal.replace(/[$,]/g, ''));
                }

                if (aVal < bVal) return currentSort.ascending ? -1 : 1;
                if (aVal > bVal) return currentSort.ascending ? 1 : -1;
                return 0;
            });

            // Update sort indicators
            document.querySelectorAll('.sort-indicator').forEach(el => el.textContent = '');
            const th = event.target.closest('th');
            if (th) {
                const indicator = th.querySelector('.sort-indicator');
                indicator.textContent = currentSort.ascending ? '▲' : '▼';
            }

            renderDashboardTable();
        }

        // ============================================
        // CREATE / UPDATE (SAVE)
        // ============================================
        function openAddInvestmentModal() {
            document.getElementById('modalTitle').textContent = 'Add New Investment';
            document.getElementById('investmentForm').reset();
            document.getElementById('investmentId').value = '';
            document.getElementById('investmentModal').style.display = 'block';
        }

        function editInvestment(id) {
            const investment = investments.find(inv => inv.id === id);
            if (!investment) return;

            document.getElementById('modalTitle').textContent = 'Edit Investment';
            document.getElementById('investmentId').value = investment.id;
            document.getElementById('companyName').value = investment.company;
            document.getElementById('industry').value = investment.industry;
            document.getElementById('fundingRound').value = investment.fundingRound;
            document.getElementById('amountRequested').value = investment.amount;

            document.getElementById('investmentModal').style.display = 'block';
        }

        function saveInvestment(event) {
            event.preventDefault();

            const id = document.getElementById('investmentId').value;
            const investmentData = {
                company: document.getElementById('companyName').value,
                industry: document.getElementById('industry').value,
                fundingRound: document.getElementById('fundingRound').value,
                amount: document.getElementById('amountRequested').value,
                iaiScore: Math.floor(Math.random() * 30) + 70,
                status: "Pending Analysis",
                lastUpdated: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
            };

            if (id) {
                // UPDATE existing
                const index = investments.findIndex(inv => inv.id === parseInt(id));
                if (index !== -1) {
                    investments[index] = { ...investments[index], ...investmentData };
                }
            } else {
                // CREATE new
                investmentData.id = Math.max(0, ...investments.map(i => i.id)) + 1;
                investments.push(investmentData);
            }

            renderDashboardTable();
            closeInvestmentModal();

            // API Integration point:
            // const method = id ? 'PUT' : 'POST';
            // const url = id ? `/api/investments/${id}` : '/api/investments';
            // fetch(url, {
            //     method: method,
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify(investmentData)
            // });
        }

        function closeInvestmentModal() {
            document.getElementById('investmentModal').style.display = 'none';
            document.getElementById('investmentForm').reset();
        }

        // ============================================
        // DELETE
        // ============================================
        function deleteInvestment(id) {
            if (!confirm('Are you sure you want to delete this investment? This action cannot be undone.')) {
                return;
            }

            const index = investments.findIndex(inv => inv.id === id);
            if (index !== -1) {
                investments.splice(index, 1);
                renderDashboardTable();
            }

            // API Integration point:
            // fetch(`/api/investments/${id}`, {
            //     method: 'DELETE'
            // });
        }

        // ============================================
        // HELPER FUNCTIONS
        // ============================================
        function getScoreColor(score) {
            if (score >= 85) return 'var(--accent-green)';
            if (score >= 70) return 'var(--accent-cyan)';
            if (score >= 55) return 'var(--accent-orange)';
            return '#EF5350';
        }

        function getStatusClass(status) {
            const statusMap = {
                'Excellent': 'status-excellent',
                'Good': 'status-good',
                'Average': 'status-average',
                'Weak': 'status-weak',
                'Pending Analysis': 'status-average'
            };
            return statusMap[status] || 'status-average';
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('investmentModal');
            if (event.target === modal) {
                closeInvestmentModal();
            }
        }

        // Initialize dashboard on page load
        renderDashboardTable();

        // ============================================
        // API INTEGRATION ENDPOINTS (for reference)
        // ============================================
        /*
        1. GET    /api/investments           - Fetch all investments
        2. POST   /api/investments           - Create new investment
        3. GET    /api/investments/:id       - Get single investment
        4. PUT    /api/investments/:id       - Update investment
        5. DELETE /api/investments/:id       - Delete investment
        6. POST   /api/documents/due-diligence - Generate document
        */
