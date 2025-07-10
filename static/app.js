// Lookman Application JavaScript

// Global variables
let currentUser = null;
let authToken = null;

// API base URL
const API_BASE = '/api';

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_BASE}/auth/check-auth`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.authenticated) {
            currentUser = data.user;
            showMainInterface();
            loadDashboard();
        } else {
            showLoginInterface();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLoginInterface();
    }
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            
            // Check for first login
            if (data.first_login) {
                showAlert(data.message + ' Please visit Profile Management to change your password.', 'warning');
                // Show a more prominent notification for first login
                showFirstLoginNotification();
            } else {
                showAlert('Login successful!', 'success');
            }
            
            showMainInterface();
            loadDashboard();
        } else {
            showAlert(data.error || 'Login failed', 'danger');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAlert('Login failed. Please try again.', 'danger');
    }
}

// Handle logout
async function logout() {
    try {
        await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        currentUser = null;
        showLoginInterface();
        showAlert('Logged out successfully', 'info');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Show login interface
function showLoginInterface() {
    document.getElementById('loginSection').style.display = 'block';
    hideAllContentSections();
    document.querySelector('.navbar').style.display = 'none';
}

// Show main interface
function showMainInterface() {
    document.getElementById('loginSection').style.display = 'none';
    document.querySelector('.navbar').style.display = 'block';
    
    // Update user info in navbar
    document.getElementById('currentUserName').textContent = currentUser.full_name;
    
    // Show/hide admin-only elements
    const adminElements = document.querySelectorAll('.admin-only');
    adminElements.forEach(element => {
        element.style.display = currentUser.role === 'admin' ? 'block' : 'none';
    });
    
    // Show dashboard by default
    showSection('dashboard');
}

// Show specific section
function showSection(sectionName) {
    hideAllContentSections();
    
    const section = document.getElementById(sectionName + 'Section');
    if (section) {
        section.style.display = 'block';
        section.classList.add('fade-in');
        
        // Load section-specific data
        switch (sectionName) {
            case 'dashboard':
                loadDashboard();
                break;
            case 'borrowers':
                loadBorrowers();
                break;
            case 'loans':
                loadLoans();
                break;
            case 'payments':
                loadPayments();
                break;
            case 'users':
                loadUsers();
                break;
            case 'reports':
                loadReports();
                break;
            case 'profile':
                loadProfile();
                break;
        }
    }
}

// Hide all content sections
function hideAllContentSections() {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.style.display = 'none';
        section.classList.remove('fade-in');
    });
}

// Load dashboard data
async function loadDashboard() {
    try {
        // Load dashboard statistics
        const statsResponse = await fetch(`${API_BASE}/admin/dashboard/stats`, {
            credentials: 'include'
        });
        
        if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            updateDashboardStats(statsData.stats);
        }
        
        // Load recent loans
        const loansResponse = await fetch(`${API_BASE}/loans?limit=5`, {
            credentials: 'include'
        });
        
        if (loansResponse.ok) {
            const loansData = await loansResponse.json();
            updateRecentLoans(loansData.loans);
        }
        
        // Load today's payments
        const paymentsResponse = await fetch(`${API_BASE}/payments/today`, {
            credentials: 'include'
        });
        
        if (paymentsResponse.ok) {
            const paymentsData = await paymentsResponse.json();
            updateTodayPayments(paymentsData);
        }
        
    } catch (error) {
        console.error('Dashboard load error:', error);
        showAlert('Failed to load dashboard data', 'warning');
    }
}

// Update dashboard statistics
function updateDashboardStats(stats) {
    document.getElementById('totalLoans').textContent = stats.total_loans || 0;
    document.getElementById('activeLoans').textContent = stats.active_loans || 0;
    document.getElementById('overdueLoans').textContent = stats.overdue_loans || 0;
    document.getElementById('totalCollections').textContent = formatCurrency(stats.total_collections || 0);
}

// Update recent loans
function updateRecentLoans(loans) {
    const container = document.getElementById('recentLoans');
    
    if (!loans || loans.length === 0) {
        container.innerHTML = '<p class="text-muted">No recent loans</p>';
        return;
    }
    
    const html = loans.slice(0, 5).map(loan => `
        <div class="d-flex justify-content-between align-items-center mb-2 p-2 border-bottom">
            <div>
                <strong>${loan.borrower_name}</strong><br>
                <small class="text-muted">${formatCurrency(loan.principal_amount)}</small>
            </div>
            <span class="badge status-${loan.status}">${loan.status}</span>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Update today's payments
function updateTodayPayments(paymentsData) {
    const container = document.getElementById('todayPayments');
    
    if (!paymentsData.payments || paymentsData.payments.length === 0) {
        container.innerHTML = '<p class="text-muted">No payments today</p>';
        return;
    }
    
    const html = paymentsData.payments.slice(0, 5).map(payment => `
        <div class="d-flex justify-content-between align-items-center mb-2 p-2 border-bottom">
            <div>
                <strong>Loan #${payment.loan_id}</strong><br>
                <small class="text-muted">Day ${payment.payment_day}</small>
            </div>
            <span class="text-success">${formatCurrency(payment.actual_amount)}</span>
        </div>
    `).join('');
    
    container.innerHTML = html + `
        <div class="mt-3 p-2 bg-light rounded">
            <small>
                <strong>Total Expected:</strong> ${formatCurrency(paymentsData.summary.total_expected)}<br>
                <strong>Total Collected:</strong> ${formatCurrency(paymentsData.summary.total_collected)}<br>
                <strong>Collection Rate:</strong> ${paymentsData.summary.collection_rate.toFixed(1)}%
            </small>
        </div>
    `;
}

// Borrower management variables
let allBorrowers = [];
let borrowerToDelete = null;

// Load borrowers data
async function loadBorrowers() {
    try {
        showAlert('Loading borrowers...', 'info');
        
        const response = await apiCall('/borrowers');
        allBorrowers = response.borrowers || [];
        
        displayBorrowers(allBorrowers);
        
        if (allBorrowers.length === 0) {
            showAlert('No borrowers found. Add your first borrower!', 'info');
        }
        
    } catch (error) {
        console.error('Failed to load borrowers:', error);
        showAlert('Failed to load borrowers: ' + error.message, 'danger');
        displayBorrowers([]);
    }
}

// Display borrowers in table
function displayBorrowers(borrowers) {
    const tbody = document.getElementById('borrowersTableBody');
    
    if (!borrowers || borrowers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <p class="text-muted mb-0">No borrowers found</p>
                    <button class="btn btn-primary mt-2" onclick="showAddBorrowerModal()">
                        <i class="fas fa-plus me-1"></i>Add First Borrower
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = borrowers.map(borrower => `
        <tr>
            <td>${borrower.id}</td>
            <td>
                <strong>${borrower.name}</strong>
            </td>
            <td>${borrower.phone || 'N/A'}</td>
            <td>${borrower.address ? (borrower.address.length > 50 ? borrower.address.substring(0, 50) + '...' : borrower.address) : 'N/A'}</td>
            <td>${formatDate(borrower.created_at)}</td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-info" onclick="viewBorrower(${borrower.id})" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-primary" onclick="editBorrower(${borrower.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="createLoanForBorrower(${borrower.id})" title="Create Loan">
                        <i class="fas fa-handshake"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteBorrower(${borrower.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

// Show add borrower modal
function showAddBorrowerModal() {
    // Clear form
    document.getElementById('addBorrowerForm').reset();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addBorrowerModal'));
    modal.show();
}

// Save new borrower
async function saveBorrower() {
    try {
        const name = document.getElementById('borrowerName').value.trim();
        const phone = document.getElementById('borrowerPhone').value.trim();
        const address = document.getElementById('borrowerAddress').value.trim();
        
        // Validation
        if (!name) {
            showAlert('Borrower name is required', 'warning');
            return;
        }
        
        if (name.length < 2) {
            showAlert('Borrower name must be at least 2 characters long', 'warning');
            return;
        }
        
        const borrowerData = {
            name: name,
            phone: phone || null,
            address: address || null
        };
        
        const response = await apiCall('/borrowers', {
            method: 'POST',
            body: JSON.stringify(borrowerData)
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('addBorrowerModal')).hide();
        
        // Reload borrowers
        await loadBorrowers();
        
        showAlert(response.message || 'Borrower created successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save borrower:', error);
        showAlert('Failed to save borrower: ' + error.message, 'danger');
    }
}

// View borrower details
async function viewBorrower(borrowerId) {
    try {
        const response = await apiCall(`/borrowers/${borrowerId}`);
        const borrower = response.borrower;
        
        // Get borrower's loans
        const loansResponse = await apiCall(`/borrowers/${borrowerId}/loans`);
        const loans = loansResponse.loans || [];
        
        const detailsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-user me-2"></i>Personal Information</h6>
                    <table class="table table-sm">
                        <tr><th>ID:</th><td>${borrower.id}</td></tr>
                        <tr><th>Name:</th><td>${borrower.name}</td></tr>
                        <tr><th>Phone:</th><td>${borrower.phone || 'N/A'}</td></tr>
                        <tr><th>Address:</th><td>${borrower.address || 'N/A'}</td></tr>
                        <tr><th>Created:</th><td>${formatDateTime(borrower.created_at)}</td></tr>
                        <tr><th>Updated:</th><td>${formatDateTime(borrower.updated_at)}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-handshake me-2"></i>Loan History</h6>
                    ${loans.length > 0 ? `
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${loans.map(loan => `
                                        <tr>
                                            <td>${loan.id}</td>
                                            <td>${formatCurrency(loan.principal_amount)}</td>
                                            <td><span class="badge status-${loan.status}">${loan.status}</span></td>
                                            <td>${formatDate(loan.start_date)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : '<p class="text-muted">No loans found</p>'}
                    <button class="btn btn-success btn-sm mt-2" onclick="createLoanForBorrower(${borrower.id})">
                        <i class="fas fa-plus me-1"></i>Create New Loan
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('borrowerDetails').innerHTML = detailsHtml;
        
        const modal = new bootstrap.Modal(document.getElementById('viewBorrowerModal'));
        modal.show();
        
    } catch (error) {
        console.error('Failed to load borrower details:', error);
        showAlert('Failed to load borrower details: ' + error.message, 'danger');
    }
}

// Edit borrower
function editBorrower(borrowerId) {
    const borrower = allBorrowers.find(b => b.id === borrowerId);
    
    if (!borrower) {
        showAlert('Borrower not found', 'error');
        return;
    }
    
    // Populate form
    document.getElementById('editBorrowerId').value = borrower.id;
    document.getElementById('editBorrowerName').value = borrower.name;
    document.getElementById('editBorrowerPhone').value = borrower.phone || '';
    document.getElementById('editBorrowerAddress').value = borrower.address || '';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editBorrowerModal'));
    modal.show();
}

// Update borrower
async function updateBorrower() {
    try {
        const borrowerId = document.getElementById('editBorrowerId').value;
        const name = document.getElementById('editBorrowerName').value.trim();
        const phone = document.getElementById('editBorrowerPhone').value.trim();
        const address = document.getElementById('editBorrowerAddress').value.trim();
        
        // Validation
        if (!name) {
            showAlert('Borrower name is required', 'warning');
            return;
        }
        
        if (name.length < 2) {
            showAlert('Borrower name must be at least 2 characters long', 'warning');
            return;
        }
        
        const borrowerData = {
            name: name,
            phone: phone || null,
            address: address || null
        };
        
        const response = await apiCall(`/borrowers/${borrowerId}`, {
            method: 'PUT',
            body: JSON.stringify(borrowerData)
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('editBorrowerModal')).hide();
        
        // Reload borrowers
        await loadBorrowers();
        
        showAlert(response.message || 'Borrower updated successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to update borrower:', error);
        showAlert('Failed to update borrower: ' + error.message, 'danger');
    }
}

// Delete borrower
function deleteBorrower(borrowerId) {
    const borrower = allBorrowers.find(b => b.id === borrowerId);
    
    if (!borrower) {
        showAlert('Borrower not found', 'error');
        return;
    }
    
    borrowerToDelete = borrowerId;
    
    // Show confirmation modal
    const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    modal.show();
}

// Confirm delete borrower
async function confirmDeleteBorrower() {
    if (!borrowerToDelete) return;
    
    try {
        const response = await apiCall(`/borrowers/${borrowerToDelete}`, {
            method: 'DELETE'
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal')).hide();
        
        // Reload borrowers
        await loadBorrowers();
        
        showAlert(response.message || 'Borrower deleted successfully!', 'success');
        
        borrowerToDelete = null;
        
    } catch (error) {
        console.error('Failed to delete borrower:', error);
        showAlert('Failed to delete borrower: ' + error.message, 'danger');
    }
}

// Filter borrowers
function filterBorrowers() {
    const searchTerm = document.getElementById('borrowerSearch').value.toLowerCase();
    
    if (!searchTerm) {
        displayBorrowers(allBorrowers);
        return;
    }
    
    const filtered = allBorrowers.filter(borrower => 
        borrower.name.toLowerCase().includes(searchTerm) ||
        (borrower.phone && borrower.phone.toLowerCase().includes(searchTerm)) ||
        (borrower.address && borrower.address.toLowerCase().includes(searchTerm))
    );
    
    displayBorrowers(filtered);
}

// Export borrowers
function exportBorrowers() {
    if (!allBorrowers || allBorrowers.length === 0) {
        showAlert('No borrowers to export', 'warning');
        return;
    }
    
    // Create CSV content
    const headers = ['ID', 'Name', 'Phone', 'Address', 'Created Date'];
    const csvContent = [
        headers.join(','),
        ...allBorrowers.map(borrower => [
            borrower.id,
            `"${borrower.name}"`,
            borrower.phone || '',
            `"${(borrower.address || '').replace(/"/g, '""')}"`,
            formatDate(borrower.created_at)
        ].join(','))
    ].join('\n');
    
    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `borrowers_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showAlert('Borrowers exported successfully!', 'success');
}

// Create loan for borrower (placeholder)
function createLoanForBorrower(borrowerId) {
    showAlert('Loan creation will be implemented in the Loans section', 'info');
    // TODO: Navigate to loans section with pre-selected borrower
}

// ============================================================================
// LOANS MANAGEMENT
// ============================================================================

let allLoans = [];
let allBorrowersForLoans = [];

async function loadLoans() {
    try {
        showAlert('Loading loans...', 'info');
        
        // Load loans summary
        const summaryResponse = await apiCall('/loans/summary');
        updateLoansSummary(summaryResponse.summary);
        
        // Load loans list
        const loansResponse = await apiCall('/loans');
        allLoans = loansResponse.loans || [];
        
        // Load borrowers for dropdown
        const borrowersResponse = await apiCall('/borrowers');
        allBorrowersForLoans = borrowersResponse.borrowers || [];
        
        displayLoans(allLoans);
        populateLoanBorrowerFilter();
        
        if (allLoans.length === 0) {
            showAlert('No loans found. Create your first loan!', 'info');
        }
        
    } catch (error) {
        console.error('Failed to load loans:', error);
        showAlert('Failed to load loans: ' + error.message, 'danger');
        displayLoans([]);
    }
}

function updateLoansSummary(summary) {
    document.getElementById('loansTotalCount').textContent = summary.total_loans || 0;
    document.getElementById('loansActiveCount').textContent = summary.active_loans || 0;
    document.getElementById('loansOverdueCount').textContent = summary.overdue_loans || 0;
    document.getElementById('loansOutstandingAmount').textContent = formatCurrency(summary.total_outstanding || 0);
}

function displayLoans(loans) {
    const tbody = document.getElementById('loansTableBody');
    
    if (!loans || loans.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
                    <i class="fas fa-handshake fa-3x text-muted mb-3"></i>
                    <p class="text-muted mb-0">No loans found</p>
                    <button class="btn btn-primary mt-2" onclick="showAddLoanModal()">
                        <i class="fas fa-plus me-1"></i>Create First Loan
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = loans.map(loan => {
        const borrower = allBorrowersForLoans.find(b => b.id === loan.borrower_id);
        const statusClass = {
            'active': 'success',
            'completed': 'primary',
            'overdue': 'warning',
            'defaulted': 'danger'
        }[loan.status] || 'secondary';
        
        return `
            <tr>
                <td>${loan.id}</td>
                <td><strong>${borrower ? borrower.name : 'Unknown'}</strong></td>
                <td>${formatCurrency(loan.principal_amount)}</td>
                <td>${loan.interest_rate}%</td>
                <td>${formatCurrency(loan.total_amount)}</td>
                <td>${formatCurrency(loan.outstanding_balance)}</td>
                <td><span class="badge bg-${statusClass}">${loan.status}</span></td>
                <td>${formatDate(loan.start_date)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-info" onclick="viewLoanDetails(${loan.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="viewLoanSchedule(${loan.id})" title="Payment Schedule">
                            <i class="fas fa-calendar"></i>
                        </button>
                        ${loan.status === 'active' ? `
                            <button class="btn btn-outline-warning" onclick="recordLoanPayment(${loan.id})" title="Record Payment">
                                <i class="fas fa-credit-card"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function populateLoanBorrowerFilter() {
    const select = document.getElementById('loanBorrowerFilter');
    select.innerHTML = '<option value="">All Borrowers</option>' + 
        allBorrowersForLoans.map(borrower => `
            <option value="${borrower.id}">${borrower.name}</option>
        `).join('');
}

function filterLoans() {
    const searchTerm = document.getElementById('loanSearch').value.toLowerCase();
    const statusFilter = document.getElementById('loanStatusFilter').value;
    const borrowerFilter = document.getElementById('loanBorrowerFilter').value;
    
    let filtered = allLoans;
    
    if (searchTerm) {
        filtered = filtered.filter(loan => {
            const borrower = allBorrowersForLoans.find(b => b.id === loan.borrower_id);
            return loan.id.toString().includes(searchTerm) ||
                   (borrower && borrower.name.toLowerCase().includes(searchTerm));
        });
    }
    
    if (statusFilter) {
        filtered = filtered.filter(loan => loan.status === statusFilter);
    }
    
    if (borrowerFilter) {
        filtered = filtered.filter(loan => loan.borrower_id.toString() === borrowerFilter);
    }
    
    displayLoans(filtered);
}

function showAddLoanModal() {
    // Load borrowers for dropdown
    const select = document.getElementById('loanBorrowerId');
    select.innerHTML = '<option value="">Select Borrower</option>' + 
        allBorrowersForLoans.map(borrower => `
            <option value="${borrower.id}">${borrower.name}</option>
        `).join('');
    
    // Set default start date to today
    document.getElementById('loanStartDate').value = new Date().toISOString().split('T')[0];
    
    // Clear form
    document.getElementById('addLoanForm').reset();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addLoanModal'));
    modal.show();
}

async function saveLoan() {
    try {
        const borrowerId = document.getElementById('loanBorrowerId').value;
        const principalAmount = parseFloat(document.getElementById('loanPrincipalAmount').value);
        const interestRate = parseFloat(document.getElementById('loanInterestRate').value);
        const expenses = parseFloat(document.getElementById('loanExpenses').value) || 0;
        const durationDays = parseInt(document.getElementById('loanDurationDays').value);
        const startDate = document.getElementById('loanStartDate').value;
        
        // Validation
        if (!borrowerId) {
            showAlert('Please select a borrower', 'warning');
            return;
        }
        
        if (!principalAmount || principalAmount <= 0) {
            showAlert('Principal amount must be greater than 0', 'warning');
            return;
        }
        
        if (!startDate) {
            showAlert('Start date is required', 'warning');
            return;
        }
        
        const loanData = {
            borrower_id: parseInt(borrowerId),
            principal_amount: principalAmount,
            interest_rate: interestRate,
            expenses: expenses,
            loan_duration_days: durationDays,
            start_date: startDate
        };
        
        const response = await apiCall('/loans', {
            method: 'POST',
            body: JSON.stringify(loanData)
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('addLoanModal')).hide();
        
        // Reload loans
        await loadLoans();
        
        showAlert(response.message || 'Loan created successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save loan:', error);
        showAlert('Failed to save loan: ' + error.message, 'danger');
    }
}

// ============================================================================
// PAYMENTS MANAGEMENT
// ============================================================================

let allPayments = [];
let allLoansForPayments = [];

async function loadPayments() {
    try {
        showAlert('Loading payments...', 'info');
        
        // Load today's payments summary
        const todayResponse = await apiCall('/payments/today');
        updatePaymentsSummary(todayResponse);
        
        // Load all payments
        const paymentsResponse = await apiCall('/payments');
        allPayments = paymentsResponse.payments || [];
        
        // Load active loans for dropdown
        const loansResponse = await apiCall('/loans?status=active');
        allLoansForPayments = loansResponse.loans || [];
        
        // Load overdue count
        const overdueResponse = await apiCall('/payments/overdue');
        document.getElementById('overduePaymentsCount').textContent = overdueResponse.total_overdue || 0;
        
        displayPayments(allPayments);
        populatePaymentLoanFilter();
        
    } catch (error) {
        console.error('Failed to load payments:', error);
        showAlert('Failed to load payments: ' + error.message, 'danger');
        displayPayments([]);
    }
}

function updatePaymentsSummary(todayData) {
    const summary = todayData.summary || {};
    document.getElementById('todayExpectedPayments').textContent = formatCurrency(summary.total_expected || 0);
    document.getElementById('todayCollectedPayments').textContent = formatCurrency(summary.total_collected || 0);
    document.getElementById('todayCollectionRate').textContent = `${(summary.collection_rate || 0).toFixed(1)}%`;
}

function displayPayments(payments) {
    const tbody = document.getElementById('paymentsTableBody');
    
    if (!payments || payments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center py-4">
                    <i class="fas fa-credit-card fa-3x text-muted mb-3"></i>
                    <p class="text-muted mb-0">No payments found</p>
                    <button class="btn btn-primary mt-2" onclick="showRecordPaymentModal()">
                        <i class="fas fa-plus me-1"></i>Record First Payment
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = payments.map(payment => {
        const loan = allLoansForPayments.find(l => l.id === payment.loan_id);
        const borrower = allBorrowersForLoans.find(b => b.id === loan?.borrower_id);
        const difference = payment.actual_amount - payment.expected_amount;
        const diffClass = difference >= 0 ? 'text-success' : 'text-danger';
        const statusClass = payment.actual_amount >= payment.expected_amount ? 'success' : 'warning';
        
        return `
            <tr>
                <td>${payment.id}</td>
                <td>${payment.loan_id}</td>
                <td>${borrower ? borrower.name : 'Unknown'}</td>
                <td>${payment.payment_day}</td>
                <td>${formatDate(payment.payment_date)}</td>
                <td>${formatCurrency(payment.expected_amount)}</td>
                <td>${formatCurrency(payment.actual_amount)}</td>
                <td class="${diffClass}">${formatCurrency(Math.abs(difference))} ${difference >= 0 ? '↑' : '↓'}</td>
                <td><span class="badge bg-${statusClass}">${payment.actual_amount >= payment.expected_amount ? 'Complete' : 'Partial'}</span></td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="editPayment(${payment.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deletePayment(${payment.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function populatePaymentLoanFilter() {
    const select = document.getElementById('paymentLoanFilter');
    select.innerHTML = '<option value="">All Loans</option>' + 
        allLoansForPayments.map(loan => {
            const borrower = allBorrowersForLoans.find(b => b.id === loan.borrower_id);
            return `<option value="${loan.id}">Loan #${loan.id} - ${borrower ? borrower.name : 'Unknown'}</option>`;
        }).join('');
}

function filterPayments() {
    const searchTerm = document.getElementById('paymentSearch').value.toLowerCase();
    const dateFilter = document.getElementById('paymentDateFilter').value;
    const loanFilter = document.getElementById('paymentLoanFilter').value;
    
    let filtered = allPayments;
    
    if (searchTerm) {
        filtered = filtered.filter(payment => {
            const loan = allLoansForPayments.find(l => l.id === payment.loan_id);
            const borrower = allBorrowersForLoans.find(b => b.id === loan?.borrower_id);
            return payment.id.toString().includes(searchTerm) ||
                   payment.loan_id.toString().includes(searchTerm) ||
                   (borrower && borrower.name.toLowerCase().includes(searchTerm));
        });
    }
    
    if (dateFilter) {
        filtered = filtered.filter(payment => payment.payment_date === dateFilter);
    }
    
    if (loanFilter) {
        filtered = filtered.filter(payment => payment.loan_id.toString() === loanFilter);
    }
    
    displayPayments(filtered);
}

function showRecordPaymentModal() {
    // Load active loans for dropdown
    const select = document.getElementById('paymentLoanId');
    select.innerHTML = '<option value="">Select Loan</option>' + 
        allLoansForPayments.map(loan => {
            const borrower = allBorrowersForLoans.find(b => b.id === loan.borrower_id);
            return `<option value="${loan.id}" data-daily="${loan.daily_repayment}">Loan #${loan.id} - ${borrower ? borrower.name : 'Unknown'} (₦${loan.daily_repayment}/day)</option>`;
        }).join('');
    
    // Set default payment date to today
    document.getElementById('paymentDate').value = new Date().toISOString().split('T')[0];
    
    // Clear form
    document.getElementById('recordPaymentForm').reset();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('recordPaymentModal'));
    modal.show();
}

// Auto-fill expected amount when loan is selected
document.addEventListener('DOMContentLoaded', function() {
    const loanSelect = document.getElementById('paymentLoanId');
    if (loanSelect) {
        loanSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const dailyAmount = selectedOption.getAttribute('data-daily');
            if (dailyAmount) {
                document.getElementById('paymentActualAmount').value = dailyAmount;
            }
        });
    }
});

async function savePayment() {
    try {
        const loanId = document.getElementById('paymentLoanId').value;
        const paymentDay = parseInt(document.getElementById('paymentDay').value);
        const paymentDate = document.getElementById('paymentDate').value;
        const actualAmount = parseFloat(document.getElementById('paymentActualAmount').value);
        const notes = document.getElementById('paymentNotes').value.trim();
        
        // Validation
        if (!loanId) {
            showAlert('Please select a loan', 'warning');
            return;
        }
        
        if (!paymentDay || paymentDay < 1) {
            showAlert('Payment day must be 1 or greater', 'warning');
            return;
        }
        
        if (!paymentDate) {
            showAlert('Payment date is required', 'warning');
            return;
        }
        
        if (actualAmount < 0) {
            showAlert('Payment amount cannot be negative', 'warning');
            return;
        }
        
        const paymentData = {
            loan_id: parseInt(loanId),
            payment_day: paymentDay,
            payment_date: paymentDate,
            actual_amount: actualAmount,
            notes: notes || null
        };
        
        const response = await apiCall('/payments', {
            method: 'POST',
            body: JSON.stringify(paymentData)
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('recordPaymentModal')).hide();
        
        // Reload payments
        await loadPayments();
        
        showAlert(response.message || 'Payment recorded successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save payment:', error);
        showAlert('Failed to save payment: ' + error.message, 'danger');
    }
}

async function loadOverduePayments() {
    try {
        const response = await apiCall('/payments/overdue');
        const overduePayments = response.overdue_payments || [];
        
        // Filter and display only overdue payments
        const tbody = document.getElementById('paymentsTableBody');
        
        if (overduePayments.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" class="text-center py-4">
                        <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                        <p class="text-muted mb-0">No overdue payments found!</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = overduePayments.map(overdue => `
            <tr class="table-warning">
                <td>-</td>
                <td>${overdue.loan_id}</td>
                <td>${overdue.borrower_name}</td>
                <td>${overdue.payment_day}</td>
                <td>${formatDate(overdue.expected_date)}</td>
                <td>${formatCurrency(overdue.expected_amount)}</td>
                <td>${formatCurrency(overdue.actual_amount)}</td>
                <td class="text-danger">${formatCurrency(overdue.expected_amount - overdue.actual_amount)} ↓</td>
                <td><span class="badge bg-danger">${overdue.days_overdue} days overdue</span></td>
                <td>
                    <button class="btn btn-warning btn-sm" onclick="recordOverduePayment(${overdue.loan_id}, ${overdue.payment_day})" title="Record Payment">
                        <i class="fas fa-credit-card"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
        showAlert(`Found ${overduePayments.length} overdue payments`, 'warning');
        
    } catch (error) {
        console.error('Failed to load overdue payments:', error);
        showAlert('Failed to load overdue payments: ' + error.message, 'danger');
    }
}

function recordOverduePayment(loanId, paymentDay) {
    // Pre-fill the record payment modal with loan and day
    showRecordPaymentModal();
    document.getElementById('paymentLoanId').value = loanId;
    document.getElementById('paymentDay').value = paymentDay;
}

// ============================================================================
// USERS MANAGEMENT
// ============================================================================

let allUsers = [];
let userToDelete = null;

async function loadUsers() {
    try {
        showAlert('Loading users...', 'info');
        
        const response = await apiCall('/admin/users');
        allUsers = response.users || [];
        
        updateUsersSummary(allUsers);
        displayUsers(allUsers);
        
        if (allUsers.length === 0) {
            showAlert('No users found. Add your first user!', 'info');
        }
        
    } catch (error) {
        console.error('Failed to load users:', error);
        showAlert('Failed to load users: ' + error.message, 'danger');
        displayUsers([]);
    }
}

function updateUsersSummary(users) {
    const totalUsers = users.length;
    const activeUsers = users.filter(user => user.is_active).length;
    const adminUsers = users.filter(user => user.role === 'admin').length;
    const officerUsers = users.filter(user => user.role === 'account_officer').length;
    
    document.getElementById('totalUsersCount').textContent = totalUsers;
    document.getElementById('activeUsersCount').textContent = activeUsers;
    document.getElementById('adminUsersCount').textContent = adminUsers;
    document.getElementById('officerUsersCount').textContent = officerUsers;
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (!users || users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <p class="text-muted mb-0">No users found</p>
                    <button class="btn btn-primary mt-2" onclick="showAddUserModal()">
                        <i class="fas fa-plus me-1"></i>Add First User
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => {
        const roleClass = user.role === 'admin' ? 'primary' : 'info';
        const statusClass = user.is_active ? 'success' : 'secondary';
        
        return `
            <tr>
                <td>${user.id}</td>
                <td><strong>${user.username}</strong></td>
                <td>${user.full_name}</td>
                <td><span class="badge bg-${roleClass}">${user.role.replace('_', ' ').toUpperCase()}</span></td>
                <td><span class="badge bg-${statusClass}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${formatDate(user.created_at)}</td>
                <td>${formatDate(user.updated_at)}</td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="editUser(${user.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        ${user.id !== currentUser.id ? `
                            <button class="btn btn-outline-danger" onclick="deleteUser(${user.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function filterUsers() {
    const searchTerm = document.getElementById('userSearch').value.toLowerCase();
    const roleFilter = document.getElementById('userRoleFilter').value;
    const statusFilter = document.getElementById('userStatusFilter').value;
    
    let filtered = allUsers;
    
    if (searchTerm) {
        filtered = filtered.filter(user => 
            user.username.toLowerCase().includes(searchTerm) ||
            user.full_name.toLowerCase().includes(searchTerm)
        );
    }
    
    if (roleFilter) {
        filtered = filtered.filter(user => user.role === roleFilter);
    }
    
    if (statusFilter) {
        const isActive = statusFilter === 'active';
        filtered = filtered.filter(user => user.is_active === isActive);
    }
    
    displayUsers(filtered);
}

function showAddUserModal() {
    // Clear form
    document.getElementById('addUserForm').reset();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('addUserModal'));
    modal.show();
}

async function saveUser() {
    try {
        const username = document.getElementById('userUsername').value.trim();
        const fullName = document.getElementById('userFullName').value.trim();
        const role = document.getElementById('userRole').value;
        const password = document.getElementById('userPassword').value;
        const confirmPassword = document.getElementById('userConfirmPassword').value;
        
        // Validation
        if (!username || !fullName || !role || !password) {
            showAlert('All fields are required', 'warning');
            return;
        }
        
        if (password !== confirmPassword) {
            showAlert('Passwords do not match', 'warning');
            return;
        }
        
        if (password.length < 6) {
            showAlert('Password must be at least 6 characters long', 'warning');
            return;
        }
        
        const userData = {
            username: username,
            full_name: fullName,
            role: role,
            password: password
        };
        
        const response = await apiCall('/admin/users', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('addUserModal')).hide();
        
        // Reload users
        await loadUsers();
        
        showAlert(response.message || 'User created successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to save user:', error);
        showAlert('Failed to save user: ' + error.message, 'danger');
    }
}

function editUser(userId) {
    const user = allUsers.find(u => u.id === userId);
    
    if (!user) {
        showAlert('User not found', 'error');
        return;
    }
    
    // Populate form
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editUserFullName').value = user.full_name;
    document.getElementById('editUserRole').value = user.role;
    document.getElementById('editUserIsActive').checked = user.is_active;
    document.getElementById('editUserPassword').value = '';
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

async function updateUser() {
    try {
        const userId = document.getElementById('editUserId').value;
        const fullName = document.getElementById('editUserFullName').value.trim();
        const role = document.getElementById('editUserRole').value;
        const isActive = document.getElementById('editUserIsActive').checked;
        const password = document.getElementById('editUserPassword').value;
        
        // Validation
        if (!fullName || !role) {
            showAlert('Full name and role are required', 'warning');
            return;
        }
        
        if (password && password.length < 6) {
            showAlert('Password must be at least 6 characters long', 'warning');
            return;
        }
        
        const userData = {
            full_name: fullName,
            role: role,
            is_active: isActive
        };
        
        if (password) {
            userData.password = password;
        }
        
        const response = await apiCall(`/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
        
        // Reload users
        await loadUsers();
        
        showAlert(response.message || 'User updated successfully!', 'success');
        
    } catch (error) {
        console.error('Failed to update user:', error);
        showAlert('Failed to update user: ' + error.message, 'danger');
    }
}

function deleteUser(userId) {
    const user = allUsers.find(u => u.id === userId);
    
    if (!user) {
        showAlert('User not found', 'error');
        return;
    }
    
    if (user.id === currentUser.id) {
        showAlert('You cannot delete your own account', 'warning');
        return;
    }
    
    userToDelete = userId;
    
    // Show confirmation modal (reuse borrower delete modal)
    const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
    modal.show();
    
    // Update modal text
    document.querySelector('#deleteConfirmModal .modal-body p').textContent = 
        `Are you sure you want to delete user "${user.full_name}"?`;
}

async function confirmDeleteUser() {
    if (!userToDelete) return;
    
    try {
        const response = await apiCall(`/admin/users/${userToDelete}`, {
            method: 'DELETE'
        });
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal')).hide();
        
        // Reload users
        await loadUsers();
        
        showAlert(response.message || 'User deleted successfully!', 'success');
        
        userToDelete = null;
        
    } catch (error) {
        console.error('Failed to delete user:', error);
        showAlert('Failed to delete user: ' + error.message, 'danger');
    }
}

// ============================================================================
// REPORTS MANAGEMENT
// ============================================================================

let currentReportType = null;

async function loadReports() {
    try {
        // Load quick stats
        const statsResponse = await apiCall('/admin/dashboard/stats');
        const stats = statsResponse.stats;
        
        document.getElementById('quickStatsLoans').textContent = stats.total_loans || 0;
        document.getElementById('quickStatsCollections').textContent = formatCurrency(stats.total_collections || 0);
        document.getElementById('monthLoans').textContent = stats.total_loans || 0; // This would need a specific endpoint
        document.getElementById('monthCollections').textContent = formatCurrency(stats.month_collections || 0);
        
    } catch (error) {
        console.error('Failed to load reports data:', error);
        showAlert('Failed to load reports data: ' + error.message, 'danger');
    }
}

function showDailyCollectionsReport() {
    currentReportType = 'daily-collections';
    document.getElementById('reportTitle').textContent = 'Daily Collections Report';
    showReportFilters(false); // No user filter needed
}

function showOutstandingLoansReport() {
    currentReportType = 'outstanding-loans';
    document.getElementById('reportTitle').textContent = 'Outstanding Loans Report';
    showReportFilters(false); // No date range needed
}

function showProfitLossReport() {
    currentReportType = 'profit-loss';
    document.getElementById('reportTitle').textContent = 'Profit & Loss Report';
    showReportFilters(false);
}

function showPerformanceReport() {
    currentReportType = 'performance';
    document.getElementById('reportTitle').textContent = 'Performance Report';
    showReportFilters(true); // Show user filter
}

function showReportFilters(showUserFilter = false) {
    const filtersDiv = document.getElementById('reportFilters');
    const userFilterDiv = document.getElementById('reportUserFilterDiv');
    
    // Set default dates (current month)
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    
    document.getElementById('reportStartDate').value = firstDay.toISOString().split('T')[0];
    document.getElementById('reportEndDate').value = lastDay.toISOString().split('T')[0];
    
    if (showUserFilter) {
        userFilterDiv.style.display = 'block';
        // Populate user dropdown
        const userSelect = document.getElementById('reportUserFilter');
        userSelect.innerHTML = '<option value="">All Users</option>' + 
            allUsers.filter(user => user.role === 'account_officer').map(user => `
                <option value="${user.id}">${user.full_name}</option>
            `).join('');
    } else {
        userFilterDiv.style.display = 'none';
    }
    
    filtersDiv.style.display = 'block';
}

async function generateReport() {
    if (!currentReportType) {
        showAlert('Please select a report type first', 'warning');
        return;
    }
    
    try {
        showAlert('Generating report...', 'info');
        
        const startDate = document.getElementById('reportStartDate').value;
        const endDate = document.getElementById('reportEndDate').value;
        const userId = document.getElementById('reportUserFilter').value;
        
        let endpoint = `/reports/${currentReportType}`;
        let params = new URLSearchParams();
        
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        if (userId) params.append('user_id', userId);
        
        if (params.toString()) {
            endpoint += '?' + params.toString();
        }
        
        const response = await apiCall(endpoint);
        displayReportResults(response.report);
        
    } catch (error) {
        console.error('Failed to generate report:', error);
        showAlert('Failed to generate report: ' + error.message, 'danger');
    }
}

function displayReportResults(report) {
    const contentDiv = document.getElementById('reportContent');
    const resultsDiv = document.getElementById('reportResults');
    
    let html = '';
    
    switch (currentReportType) {
        case 'daily-collections':
            html = generateDailyCollectionsHTML(report);
            break;
        case 'outstanding-loans':
            html = generateOutstandingLoansHTML(report);
            break;
        case 'profit-loss':
            html = generateProfitLossHTML(report);
            break;
        case 'performance':
            html = generatePerformanceHTML(report);
            break;
        default:
            html = '<p class="text-muted">Report type not implemented yet.</p>';
    }
    
    contentDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    showAlert('Report generated successfully!', 'success');
}

function generateDailyCollectionsHTML(report) {
    const summary = report.summary || {};
    
    return `
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h4>${formatCurrency(summary.total_expected || 0)}</h4>
                        <small>Total Expected</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h4>${formatCurrency(summary.total_collected || 0)}</h4>
                        <small>Total Collected</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h4>${(summary.collection_rate || 0).toFixed(1)}%</h4>
                        <small>Collection Rate</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h4>${summary.payment_count || 0}</h4>
                        <small>Total Payments</small>
                    </div>
                </div>
            </div>
        </div>
        
        <h6>Officer Breakdown</h6>
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Officer</th>
                        <th>Expected</th>
                        <th>Collected</th>
                        <th>Rate</th>
                        <th>Payments</th>
                    </tr>
                </thead>
                <tbody>
                    ${(report.officer_breakdown || []).map(officer => `
                        <tr>
                            <td>${officer.officer_name}</td>
                            <td>${formatCurrency(officer.expected)}</td>
                            <td>${formatCurrency(officer.collected)}</td>
                            <td>${officer.collection_rate.toFixed(1)}%</td>
                            <td>${officer.payment_count}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function generateOutstandingLoansHTML(report) {
    const summary = report.summary || {};
    
    return `
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h4>${summary.total_loans || 0}</h4>
                        <small>Total Loans</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h4>${formatCurrency(summary.total_outstanding || 0)}</h4>
                        <small>Total Outstanding</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-danger text-white">
                    <div class="card-body text-center">
                        <h4>${formatCurrency(summary.overdue_outstanding || 0)}</h4>
                        <small>Overdue Outstanding</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h4>${(summary.overdue_percentage || 0).toFixed(1)}%</h4>
                        <small>Overdue %</small>
                    </div>
                </div>
            </div>
        </div>
        
        <h6>Outstanding Loans Details</h6>
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Loan ID</th>
                        <th>Borrower</th>
                        <th>Principal</th>
                        <th>Outstanding</th>
                        <th>Status</th>
                        <th>Days Overdue</th>
                    </tr>
                </thead>
                <tbody>
                    ${(report.loans || []).map(loan => `
                        <tr>
                            <td>${loan.id}</td>
                            <td>${loan.borrower_name || 'Unknown'}</td>
                            <td>${formatCurrency(loan.principal_amount)}</td>
                            <td>${formatCurrency(loan.outstanding_balance)}</td>
                            <td><span class="badge bg-${loan.status === 'overdue' ? 'danger' : 'warning'}">${loan.status}</span></td>
                            <td>${loan.days_overdue || 0}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function generateProfitLossHTML(report) {
    const revenue = report.revenue || {};
    const expenses = report.expenses || {};
    const profit = report.profit || {};
    
    return `
        <div class="row mb-4">
            <div class="col-md-4">
                <h6>Revenue</h6>
                <table class="table table-sm">
                    <tr><td>Principal Disbursed:</td><td class="text-end">${formatCurrency(revenue.principal_disbursed || 0)}</td></tr>
                    <tr><td>Interest Income:</td><td class="text-end">${formatCurrency(revenue.interest_income || 0)}</td></tr>
                    <tr><td>Fee Income:</td><td class="text-end">${formatCurrency(revenue.fee_income || 0)}</td></tr>
                    <tr class="table-dark"><td><strong>Gross Revenue:</strong></td><td class="text-end"><strong>${formatCurrency(revenue.gross_revenue || 0)}</strong></td></tr>
                </table>
            </div>
            <div class="col-md-4">
                <h6>Expenses</h6>
                <table class="table table-sm">
                    <tr><td>Salary Expenses:</td><td class="text-end">${formatCurrency(expenses.salary_expenses || 0)}</td></tr>
                    <tr class="table-dark"><td><strong>Total Expenses:</strong></td><td class="text-end"><strong>${formatCurrency(expenses.total_expenses || 0)}</strong></td></tr>
                </table>
            </div>
            <div class="col-md-4">
                <h6>Profitability</h6>
                <table class="table table-sm">
                    <tr><td>Gross Profit:</td><td class="text-end">${formatCurrency(profit.gross_profit || 0)}</td></tr>
                    <tr><td>Net Profit:</td><td class="text-end">${formatCurrency(profit.net_profit || 0)}</td></tr>
                    <tr class="table-dark"><td><strong>Profit Margin:</strong></td><td class="text-end"><strong>${(profit.profit_margin || 0).toFixed(1)}%</strong></td></tr>
                </table>
            </div>
        </div>
    `;
}

function generatePerformanceHTML(report) {
    return `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Officer</th>
                        <th>Total Loans</th>
                        <th>Active Loans</th>
                        <th>Completion Rate</th>
                        <th>Collection Rate</th>
                        <th>Portfolio Value</th>
                    </tr>
                </thead>
                <tbody>
                    ${(report.performance_data || []).map(data => `
                        <tr>
                            <td>${data.user.full_name}</td>
                            <td>${data.loan_metrics.total_loans}</td>
                            <td>${data.loan_metrics.active_loans}</td>
                            <td>${data.loan_metrics.completion_rate.toFixed(1)}%</td>
                            <td>${data.collection_metrics.collection_rate.toFixed(1)}%</td>
                            <td>${formatCurrency(data.portfolio_metrics.total_portfolio)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

function exportReport() {
    showAlert('Export functionality will be implemented soon', 'info');
}

function printReport() {
    const reportContent = document.getElementById('reportContent').innerHTML;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Report - ${document.getElementById('reportTitle').textContent}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { padding: 20px; }
                    .card { border: 1px solid #dee2e6; }
                    .bg-primary { background-color: #0d6efd !important; }
                    .bg-success { background-color: #198754 !important; }
                    .bg-warning { background-color: #ffc107 !important; }
                    .bg-danger { background-color: #dc3545 !important; }
                    .bg-info { background-color: #0dcaf0 !important; }
                </style>
            </head>
            <body>
                <h1>${document.getElementById('reportTitle').textContent}</h1>
                <p>Generated on: ${new Date().toLocaleString()}</p>
                ${reportContent}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Profile Management Functions
let currentProfile = null;
let currentDocumentType = null;
let cameraStream = null;

function loadProfile() {
    console.log('Loading profile...');
    loadBorrowersForProfile();
}

async function loadBorrowersForProfile() {
    try {
        const data = await apiCall('/borrowers');
        const select = document.getElementById('profileBorrowerSelect');
        select.innerHTML = '<option value="">Select a borrower to view/edit profile</option>';
        
        data.borrowers.forEach(borrower => {
            const option = document.createElement('option');
            option.value = borrower.id;
            option.textContent = `${borrower.name} (${borrower.phone || 'No phone'})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading borrowers:', error);
        showAlert('Failed to load borrowers', 'danger');
    }
}

async function loadBorrowerProfile() {
    const borrowerId = document.getElementById('profileBorrowerSelect').value;
    if (!borrowerId) {
        document.getElementById('profileContent').style.display = 'none';
        return;
    }
    
    try {
        // Load borrower profile
        const profileData = await apiCall(`/profile/borrower/${borrowerId}`);
        currentProfile = profileData.profile;
        
        // Populate form fields
        populateProfileForm(currentProfile);
        
        // Show profile content
        document.getElementById('profileContent').style.display = 'block';
        
        // Load documents
        loadDocuments();
    } catch (error) {
        console.error('Error loading profile:', error);
        if (error.message.includes('Profile not found')) {
            // Profile doesn't exist, create new one
            currentProfile = { borrower_id: borrowerId };
            clearProfileForm();
            document.getElementById('profileContent').style.display = 'block';
        } else {
            showAlert('Failed to load profile', 'danger');
        }
    }
}

function populateProfileForm(profile) {
    // Personal Information
    document.getElementById('fullName').value = profile.full_name || '';
    document.getElementById('dateOfBirth').value = profile.date_of_birth || '';
    document.getElementById('phoneNumber').value = profile.phone_number || '';
    document.getElementById('email').value = profile.email || '';
    document.getElementById('address').value = profile.address || '';
    document.getElementById('city').value = profile.city || '';
    document.getElementById('state').value = profile.state || '';
    document.getElementById('country').value = profile.country || 'Nigeria';
    document.getElementById('maritalStatus').value = profile.marital_status || '';
    
    // Identification
    document.getElementById('bvn').value = profile.bvn || '';
    document.getElementById('nin').value = profile.nin || '';
    document.getElementById('primaryIdType').value = profile.primary_id_type || '';
    document.getElementById('primaryIdNumber').value = profile.primary_id_number || '';
    
    // Employment
    document.getElementById('employmentType').value = profile.employment_type || '';
    document.getElementById('monthlyIncome').value = profile.monthly_income || '';
    document.getElementById('employerName').value = profile.employer_name || '';
    document.getElementById('jobTitle').value = profile.job_title || '';
    document.getElementById('workAddress').value = profile.work_address || '';
    document.getElementById('employmentStartDate').value = profile.employment_start_date || '';
    
    // Business Information
    document.getElementById('businessName').value = profile.business_name || '';
    document.getElementById('businessRegistrationNumber').value = profile.business_registration_number || '';
    document.getElementById('businessType').value = profile.business_type || '';
    document.getElementById('annualRevenue').value = profile.annual_revenue || '';
    document.getElementById('businessAddress').value = profile.business_address || '';
    
    // Banking
    document.getElementById('bankName').value = profile.bank_name || '';
    document.getElementById('accountNumber').value = profile.account_number || '';
    document.getElementById('accountName').value = profile.account_name || '';
    document.getElementById('accountType').value = profile.account_type || '';
    
    // Update employment fields visibility
    toggleEmploymentFields();
    
    // Update verification status displays
    updateVerificationStatus('bvn', profile.bvn_verification_status);
    updateVerificationStatus('nin', profile.id_verification_status);
}

function clearProfileForm() {
    document.getElementById('personalInfoForm').reset();
    document.getElementById('identificationForm').reset();
    document.getElementById('employmentForm').reset();
    document.getElementById('loanApplicationForm').reset();
}

function toggleEmploymentFields() {
    const employmentType = document.getElementById('employmentType').value;
    const employmentFields = document.getElementById('employmentFields');
    const businessFields = document.getElementById('businessFields');
    
    if (employmentType === 'employed') {
        employmentFields.style.display = 'block';
        businessFields.style.display = 'none';
    } else if (employmentType === 'self_employed') {
        employmentFields.style.display = 'none';
        businessFields.style.display = 'block';
    } else {
        employmentFields.style.display = 'none';
        businessFields.style.display = 'none';
    }
}

async function savePersonalInfo() {
    if (!currentProfile || !currentProfile.borrower_id) {
        showAlert('Please select a borrower first', 'warning');
        return;
    }
    
    const formData = {
        full_name: document.getElementById('fullName').value,
        date_of_birth: document.getElementById('dateOfBirth').value,
        phone_number: document.getElementById('phoneNumber').value,
        email: document.getElementById('email').value,
        address: document.getElementById('address').value,
        city: document.getElementById('city').value,
        state: document.getElementById('state').value,
        country: document.getElementById('country').value,
        marital_status: document.getElementById('maritalStatus').value
    };
    
    try {
        const data = await apiCall(`/profile/borrower/${currentProfile.borrower_id}`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        currentProfile = data.profile;
        showAlert('Personal information saved successfully', 'success');
    } catch (error) {
        console.error('Error saving personal info:', error);
        showAlert('Failed to save personal information', 'danger');
    }
}

async function saveIdentification() {
    if (!currentProfile || !currentProfile.borrower_id) {
        showAlert('Please select a borrower first', 'warning');
        return;
    }
    
    const formData = {
        bvn: document.getElementById('bvn').value,
        nin: document.getElementById('nin').value,
        primary_id_type: document.getElementById('primaryIdType').value,
        primary_id_number: document.getElementById('primaryIdNumber').value
    };
    
    try {
        const data = await apiCall(`/profile/borrower/${currentProfile.borrower_id}`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        currentProfile = data.profile;
        showAlert('Identification information saved successfully', 'success');
    } catch (error) {
        console.error('Error saving identification:', error);
        showAlert('Failed to save identification information', 'danger');
    }
}

async function saveEmployment() {
    if (!currentProfile || !currentProfile.borrower_id) {
        showAlert('Please select a borrower first', 'warning');
        return;
    }
    
    const formData = {
        employment_type: document.getElementById('employmentType').value,
        monthly_income: document.getElementById('monthlyIncome').value,
        employer_name: document.getElementById('employerName').value,
        job_title: document.getElementById('jobTitle').value,
        work_address: document.getElementById('workAddress').value,
        employment_start_date: document.getElementById('employmentStartDate').value,
        business_name: document.getElementById('businessName').value,
        business_registration_number: document.getElementById('businessRegistrationNumber').value,
        business_type: document.getElementById('businessType').value,
        annual_revenue: document.getElementById('annualRevenue').value,
        business_address: document.getElementById('businessAddress').value,
        bank_name: document.getElementById('bankName').value,
        account_number: document.getElementById('accountNumber').value,
        account_name: document.getElementById('accountName').value,
        account_type: document.getElementById('accountType').value
    };
    
    try {
        const data = await apiCall(`/profile/borrower/${currentProfile.borrower_id}`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        currentProfile = data.profile;
        showAlert('Employment information saved successfully', 'success');
    } catch (error) {
        console.error('Error saving employment info:', error);
        showAlert('Failed to save employment information', 'danger');
    }
}

async function verifyBVN() {
    const bvn = document.getElementById('bvn').value;
    if (!bvn) {
        showAlert('Please enter BVN first', 'warning');
        return;
    }
    
    try {
        const data = await apiCall('/profile/verification/bvn', {
            method: 'POST',
            body: JSON.stringify({ bvn })
        });
        
        if (data.verified) {
            updateVerificationStatus('bvn', 'verified');
            showAlert('BVN verified successfully', 'success');
            
            // Auto-fill verified data
            if (data.data) {
                if (data.data.name && !document.getElementById('fullName').value) {
                    document.getElementById('fullName').value = data.data.name;
                }
                if (data.data.date_of_birth && !document.getElementById('dateOfBirth').value) {
                    document.getElementById('dateOfBirth').value = data.data.date_of_birth;
                }
                if (data.data.phone && !document.getElementById('phoneNumber').value) {
                    document.getElementById('phoneNumber').value = data.data.phone;
                }
            }
        } else {
            updateVerificationStatus('bvn', 'rejected');
            showAlert(data.message || 'BVN verification failed', 'danger');
        }
    } catch (error) {
        console.error('Error verifying BVN:', error);
        updateVerificationStatus('bvn', 'rejected');
        showAlert('BVN verification failed', 'danger');
    }
}

async function verifyNIN() {
    const nin = document.getElementById('nin').value;
    if (!nin) {
        showAlert('Please enter NIN first', 'warning');
        return;
    }
    
    try {
        const data = await apiCall('/profile/verification/nin', {
            method: 'POST',
            body: JSON.stringify({ nin })
        });
        
        if (data.verified) {
            updateVerificationStatus('nin', 'verified');
            showAlert('NIN verified successfully', 'success');
            
            // Auto-fill verified data
            if (data.data) {
                if (data.data.name && !document.getElementById('fullName').value) {
                    document.getElementById('fullName').value = data.data.name;
                }
                if (data.data.date_of_birth && !document.getElementById('dateOfBirth').value) {
                    document.getElementById('dateOfBirth').value = data.data.date_of_birth;
                }
                if (data.data.address && !document.getElementById('address').value) {
                    document.getElementById('address').value = data.data.address;
                }
            }
        } else {
            updateVerificationStatus('nin', 'rejected');
            showAlert(data.message || 'NIN verification failed', 'danger');
        }
    } catch (error) {
        console.error('Error verifying NIN:', error);
        updateVerificationStatus('nin', 'rejected');
        showAlert('NIN verification failed', 'danger');
    }
}

function updateVerificationStatus(type, status) {
    const statusElement = document.getElementById(`${type}Status`);
    if (!statusElement) return;
    
    let statusText = '';
    let statusClass = '';
    
    switch (status) {
        case 'verified':
            statusText = '✓ Verified';
            statusClass = 'text-success';
            break;
        case 'rejected':
            statusText = '✗ Verification failed';
            statusClass = 'text-danger';
            break;
        case 'pending':
        default:
            statusText = 'Pending verification';
            statusClass = 'text-warning';
            break;
    }
    
    statusElement.textContent = statusText;
    statusElement.className = `form-text ${statusClass}`;
}

// Document Management Functions
function captureDocument(documentType) {
    currentDocumentType = documentType;
    const modal = new bootstrap.Modal(document.getElementById('documentCaptureModal'));
    modal.show();
    startCamera();
}

async function startCamera() {
    try {
        const video = document.getElementById('cameraVideo');
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } // Use back camera if available
        });
        video.srcObject = cameraStream;
    } catch (error) {
        console.error('Error accessing camera:', error);
        showAlert('Failed to access camera. Please check permissions.', 'danger');
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
}

function capturePhoto() {
    const video = document.getElementById('cameraVideo');
    const canvas = document.getElementById('captureCanvas');
    const preview = document.getElementById('previewImage');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    
    // Show preview
    preview.src = imageData;
    document.getElementById('capturedImage').style.display = 'block';
    document.getElementById('saveDocumentBtn').style.display = 'inline-block';
    
    // Stop camera
    stopCamera();
}

async function saveDocument() {
    if (!currentProfile || !currentProfile.borrower_id) {
        showAlert('Please select a borrower first', 'warning');
        return;
    }
    
    const documentName = document.getElementById('documentName').value;
    if (!documentName) {
        showAlert('Please enter a document name', 'warning');
        return;
    }
    
    const imageData = document.getElementById('previewImage').src;
    
    const documentData = {
        document_type: currentDocumentType,
        document_name: documentName,
        document_data: imageData
    };
    
    try {
        await apiCall(`/profile/borrower/${currentProfile.borrower_id}/documents`, {
            method: 'POST',
            body: JSON.stringify(documentData)
        });
        
        showAlert('Document saved successfully', 'success');
        
        // Close modal and refresh documents
        const modal = bootstrap.Modal.getInstance(document.getElementById('documentCaptureModal'));
        modal.hide();
        loadDocuments();
        
        // Reset form
        document.getElementById('documentName').value = '';
        document.getElementById('capturedImage').style.display = 'none';
        document.getElementById('saveDocumentBtn').style.display = 'none';
        
    } catch (error) {
        console.error('Error saving document:', error);
        showAlert('Failed to save document', 'danger');
    }
}

function loadDocuments() {
    if (!currentProfile || !currentProfile.documents) {
        document.getElementById('uploadedDocuments').innerHTML = '<p class="text-muted">No documents uploaded yet.</p>';
        return;
    }
    
    const documentsHtml = currentProfile.documents.map(doc => `
        <div class="card mb-2">
            <div class="card-body p-2">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${doc.document_name}</strong><br>
                        <small class="text-muted">${doc.document_type.replace('_', ' ').toUpperCase()}</small>
                    </div>
                    <div>
                        <span class="badge bg-${doc.verification_status === 'verified' ? 'success' : doc.verification_status === 'rejected' ? 'danger' : 'warning'}">
                            ${doc.verification_status}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    document.getElementById('uploadedDocuments').innerHTML = documentsHtml || '<p class="text-muted">No documents uploaded yet.</p>';
}

// Loan Application Functions
function toggleCollateralFields() {
    const hasCollateral = document.getElementById('hasCollateral').checked;
    const collateralFields = document.getElementById('collateralFields');
    collateralFields.style.display = hasCollateral ? 'block' : 'none';
}

async function submitLoanApplication() {
    if (!currentProfile || !currentProfile.borrower_id) {
        showAlert('Please select a borrower first', 'warning');
        return;
    }
    
    const formData = {
        loan_purpose: document.getElementById('loanPurpose').value,
        loan_amount: parseFloat(document.getElementById('loanAmount').value),
        loan_term: parseInt(document.getElementById('loanTerm').value),
        interest_rate: parseFloat(document.getElementById('interestRate').value),
        has_collateral: document.getElementById('hasCollateral').checked,
        collateral_type: document.getElementById('collateralType').value,
        collateral_value: parseFloat(document.getElementById('collateralValue').value) || null,
        collateral_description: document.getElementById('collateralDescription').value,
        guarantor_name: document.getElementById('guarantorName').value,
        guarantor_phone: document.getElementById('guarantorPhone').value,
        guarantor_address: document.getElementById('guarantorAddress').value,
        guarantor_relationship: document.getElementById('guarantorRelationship').value
    };
    
    // Validation
    if (!formData.loan_purpose || !formData.loan_amount || !formData.loan_term) {
        showAlert('Please fill in all required fields', 'warning');
        return;
    }
    
    try {
        await apiCall(`/profile/borrower/${currentProfile.borrower_id}/loan-application`, {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        showAlert('Loan application submitted successfully', 'success');
        
        // Reset form
        document.getElementById('loanApplicationForm').reset();
        toggleCollateralFields();
        
    } catch (error) {
        console.error('Error submitting loan application:', error);
        showAlert('Failed to submit loan application', 'danger');
    }
}

// Create New Profile Functions
function createNewBorrowerProfile() {
    const modal = new bootstrap.Modal(document.getElementById('createProfileModal'));
    modal.show();
}

async function saveNewProfile() {
    const formData = {
        name: document.getElementById('newProfileName').value,
        phone: document.getElementById('newProfilePhone').value,
        address: document.getElementById('newProfileAddress').value
    };
    
    if (!formData.name) {
        showAlert('Please enter a name', 'warning');
        return;
    }
    
    try {
        // First create the borrower
        const borrowerData = await apiCall('/borrowers', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
        
        // Then create the profile
        const profileData = {
            full_name: formData.name,
            phone_number: formData.phone,
            email: document.getElementById('newProfileEmail').value,
            address: formData.address
        };
        
        await apiCall(`/profile/borrower/${borrowerData.borrower.id}`, {
            method: 'POST',
            body: JSON.stringify(profileData)
        });
        
        showAlert('Profile created successfully', 'success');
        
        // Close modal and refresh borrowers list
        const modal = bootstrap.Modal.getInstance(document.getElementById('createProfileModal'));
        modal.hide();
        loadBorrowersForProfile();
        
        // Clear form
        document.getElementById('createProfileForm').reset();
        
        // Select the new borrower
        setTimeout(() => {
            document.getElementById('profileBorrowerSelect').value = borrowerData.borrower.id;
            loadBorrowerProfile();
        }, 500);
        
    } catch (error) {
        console.error('Error creating profile:', error);
        showAlert('Failed to create profile', 'danger');
    }
}

// Update the create loan for borrower function
function createLoanForBorrower(borrowerId) {
    showSection('loans');
    setTimeout(() => {
        showAddLoanModal();
        document.getElementById('loanBorrowerId').value = borrowerId;
    }, 500);
}

// Additional functions for loans interface
function viewLoanDetails(loanId) {
    showAlert('Loan details view will be implemented soon', 'info');
}

function viewLoanSchedule(loanId) {
    showAlert('Loan schedule view will be implemented soon', 'info');
}

function recordLoanPayment(loanId) {
    showSection('payments');
    setTimeout(() => {
        showRecordPaymentModal();
        document.getElementById('paymentLoanId').value = loanId;
    }, 500);
}

// Additional functions for payments interface
function editPayment(paymentId) {
    showAlert('Payment editing will be implemented soon', 'info');
}

function deletePayment(paymentId) {
    showAlert('Payment deletion will be implemented soon', 'info');
}

// Override the delete confirmation function to handle both borrowers and users
const originalConfirmDeleteBorrower = window.confirmDeleteBorrower;
window.confirmDeleteBorrower = function() {
    if (userToDelete) {
        confirmDeleteUser();
    } else {
        originalConfirmDeleteBorrower();
    }
};

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-NG');
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('en-NG');
}

// Show alert message
function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-custom');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-custom`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '80px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// API helper function
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API call failed');
        }
        
        return data;
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// Show first login notification
function showFirstLoginNotification() {
    // Create a prominent notification for first login
    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed';
    notificationDiv.style.top = '120px';
    notificationDiv.style.right = '20px';
    notificationDiv.style.zIndex = '10000';
    notificationDiv.style.minWidth = '400px';
    notificationDiv.style.maxWidth = '500px';
    
    notificationDiv.innerHTML = `
        <h6 class="alert-heading"><i class="fas fa-exclamation-triangle me-2"></i>Security Notice</h6>
        <p class="mb-2">This is your first login. For security reasons, please change your password immediately.</p>
        <hr>
        <div class="d-flex justify-content-between">
            <a href="user_profile.html" class="btn btn-warning btn-sm">
                <i class="fas fa-key me-1"></i>Change Password Now
            </a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(notificationDiv);
    
    // Auto-remove after 30 seconds
    setTimeout(() => {
        if (notificationDiv.parentNode) {
            notificationDiv.remove();
        }
    }, 30000);
}

// Export functions for global access
window.showSection = showSection;
window.logout = logout;

