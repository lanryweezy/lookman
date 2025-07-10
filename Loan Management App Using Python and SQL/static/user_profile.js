// User Profile Management JavaScript
let currentUser = null;
let allUsers = [];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadCurrentUser();
    checkFirstLogin();
});

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    const toast = document.createElement('div');
    toast.className = `toast ${bgClass} text-white`;
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    
    toast.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            <strong class="me-auto">Profile Management</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Handle API errors
function handleApiError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    
    if (error.status === 401) {
        showToast('Session expired. Please login again.', 'error');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    } else if (error.responseJSON && error.responseJSON.error) {
        showToast(error.responseJSON.error, 'error');
    } else {
        showToast(`An error occurred${context ? ' while ' + context : ''}. Please try again.`, 'error');
    }
}

// Load current user profile
function loadCurrentUser() {
    $.ajax({
        url: '/api/user-profile/current',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                currentUser = response.user;
                populateProfileForm(currentUser);
                
                // Show admin features if user is admin
                if (currentUser.role === 'admin') {
                    $('.admin-only').show();
                    loadAllUsers();
                }
            } else {
                handleApiError({ responseJSON: response }, 'loading profile');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'loading profile');
        }
    });
}

// Check if first login
function checkFirstLogin() {
    $.ajax({
        url: '/api/user-profile/check-first-login',
        method: 'GET',
        success: function(response) {
            if (response.success && response.is_first_login) {
                $('#firstLoginWarning').show();
                $('#currentPasswordGroup').hide();
                $('#change-password-tab').click(); // Switch to password change tab
            }
        },
        error: function(xhr, status, error) {
            console.error('Error checking first login:', error);
        }
    });
}

// Populate profile form with user data
function populateProfileForm(user) {
    $('#username').val(user.username || '');
    $('#role').val(user.role ? user.role.replace('_', ' ').toUpperCase() : '');
    $('#fullName').val(user.full_name || '');
    $('#email').val(user.email || '');
    $('#phone').val(user.phone || '');
    
    if (user.updated_at) {
        const date = new Date(user.updated_at);
        $('#lastUpdated').val(date.toLocaleString());
    }
}

// Update profile information
function updateProfile() {
    const formData = {
        full_name: $('#fullName').val().trim(),
        email: $('#email').val().trim(),
        phone: $('#phone').val().trim()
    };
    
    // Validate required fields
    if (!formData.full_name) {
        showToast('Full name is required', 'error');
        return;
    }
    
    $.ajax({
        url: '/api/user-profile/update',
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                showToast('Profile updated successfully', 'success');
                currentUser = response.user;
                populateProfileForm(currentUser);
            } else {
                handleApiError({ responseJSON: response }, 'updating profile');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'updating profile');
        }
    });
}

// Change password
function changePassword() {
    const currentPassword = $('#currentPassword').val();
    const newPassword = $('#newPassword').val();
    const confirmPassword = $('#confirmPassword').val();
    
    // Validate passwords
    if (!newPassword || !confirmPassword) {
        showToast('Please fill in all password fields', 'error');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showToast('New passwords do not match', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showToast('Password must be at least 6 characters long', 'error');
        return;
    }
    
    // Check if password contains letters and numbers
    if (!/[A-Za-z]/.test(newPassword) || !/\d/.test(newPassword)) {
        showToast('Password must contain at least one letter and one number', 'error');
        return;
    }
    
    const formData = {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword
    };
    
    $.ajax({
        url: '/api/user-profile/change-password',
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                showToast('Password changed successfully', 'success');
                // Clear form
                $('#passwordForm')[0].reset();
                $('#firstLoginWarning').hide();
                $('#currentPasswordGroup').show();
                
                // Reload user data
                loadCurrentUser();
            } else {
                handleApiError({ responseJSON: response }, 'changing password');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'changing password');
        }
    });
}

// Load profile statistics
function loadProfileStats() {
    $.ajax({
        url: '/api/user-profile/profile-stats',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                const stats = response.stats;
                
                // Update stats display
                $('#profileCompletion').text(Math.round(stats.profile_completion) + '%');
                $('#passwordAge').text(stats.password_age_days ? stats.password_age_days + ' days' : 'N/A');
                $('#accountAge').text(stats.account_age_days + ' days');
                
                // Determine security status
                let securityStatus = 'Good';
                let statusClass = 'bg-success';
                
                if (stats.is_first_login) {
                    securityStatus = 'Needs Setup';
                    statusClass = 'bg-danger';
                } else if (stats.password_age_days > 90) {
                    securityStatus = 'Update Needed';
                    statusClass = 'bg-warning';
                } else if (stats.profile_completion < 75) {
                    securityStatus = 'Incomplete';
                    statusClass = 'bg-warning';
                }
                
                $('#securityStatus').text(securityStatus);
                $('#profileStats').show();
            } else {
                handleApiError({ responseJSON: response }, 'loading statistics');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'loading statistics');
        }
    });
}

// Admin Functions

// Load all users (admin only)
function loadAllUsers() {
    $.ajax({
        url: '/api/user-profile/admin/users',
        method: 'GET',
        success: function(response) {
            if (response.success) {
                allUsers = response.users;
                displayUsers(allUsers);
            } else {
                handleApiError({ responseJSON: response }, 'loading users');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'loading users');
        }
    });
}

// Display users in table
function displayUsers(users) {
    const tbody = $('#usersTableBody');
    tbody.empty();
    
    if (users.length === 0) {
        tbody.append(`
            <tr>
                <td colspan="8" class="text-center text-muted">No users found</td>
            </tr>
        `);
        return;
    }
    
    users.forEach(user => {
        const statusBadge = user.is_active ? 
            '<span class="badge bg-success">Active</span>' : 
            '<span class="badge bg-danger">Inactive</span>';
        
        const firstLoginBadge = user.is_first_login ? 
            '<span class="badge bg-warning">Yes</span>' : 
            '<span class="badge bg-success">No</span>';
        
        const row = `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.full_name}</td>
                <td>${user.email || '-'}</td>
                <td><span class="badge bg-info">${user.role.replace('_', ' ').toUpperCase()}</span></td>
                <td>${statusBadge}</td>
                <td>${firstLoginBadge}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary" onclick="editUser(${user.id})" title="Edit User">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="resetPassword(${user.id})" title="Reset Password">
                            <i class="fas fa-key"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-${user.is_active ? 'danger' : 'success'}" 
                                onclick="toggleUserStatus(${user.id})" 
                                title="${user.is_active ? 'Deactivate' : 'Activate'} User">
                            <i class="fas fa-${user.is_active ? 'ban' : 'check'}"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

// Filter users
function filterUsers() {
    const searchTerm = $('#userSearch').val().toLowerCase();
    const roleFilter = $('#roleFilter').val();
    
    let filteredUsers = allUsers.filter(user => {
        const matchesSearch = user.username.toLowerCase().includes(searchTerm) ||
                            user.full_name.toLowerCase().includes(searchTerm) ||
                            (user.email && user.email.toLowerCase().includes(searchTerm));
        
        const matchesRole = !roleFilter || user.role === roleFilter;
        
        return matchesSearch && matchesRole;
    });
    
    displayUsers(filteredUsers);
}

// Show create user modal
function showCreateUserModal() {
    $('#createUserForm')[0].reset();
    $('#createUserModal').modal('show');
}

// Create new user
function createUser() {
    const formData = {
        username: $('#newUsername').val().trim(),
        full_name: $('#newFullName').val().trim(),
        email: $('#newEmail').val().trim(),
        phone: $('#newPhone').val().trim(),
        role: $('#newRole').val(),
        password: $('#newPassword').val(),
        is_active: $('#newIsActive').is(':checked')
    };
    
    // Validate required fields
    if (!formData.username || !formData.full_name || !formData.role || !formData.password) {
        showToast('Please fill in all required fields', 'error');
        return;
    }
    
    // Validate password confirmation
    const confirmPassword = $('#newConfirmPassword').val();
    if (formData.password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
    }
    
    $.ajax({
        url: '/api/user-profile/admin/user/create',
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                showToast('User created successfully', 'success');
                $('#createUserModal').modal('hide');
                loadAllUsers(); // Refresh users list
            } else {
                handleApiError({ responseJSON: response }, 'creating user');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'creating user');
        }
    });
}

// Edit user
function editUser(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    // Populate edit form
    $('#editUserId').val(user.id);
    $('#editFullName').val(user.full_name);
    $('#editEmail').val(user.email || '');
    $('#editPhone').val(user.phone || '');
    $('#editRole').val(user.role);
    $('#editIsActive').prop('checked', user.is_active);
    
    $('#editUserModal').modal('show');
}

// Update user
function updateUser() {
    const userId = $('#editUserId').val();
    const formData = {
        full_name: $('#editFullName').val().trim(),
        email: $('#editEmail').val().trim(),
        phone: $('#editPhone').val().trim(),
        role: $('#editRole').val(),
        is_active: $('#editIsActive').is(':checked')
    };
    
    // Validate required fields
    if (!formData.full_name || !formData.role) {
        showToast('Please fill in all required fields', 'error');
        return;
    }
    
    $.ajax({
        url: `/api/user-profile/admin/user/${userId}/update`,
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                showToast('User updated successfully', 'success');
                $('#editUserModal').modal('hide');
                loadAllUsers(); // Refresh users list
            } else {
                handleApiError({ responseJSON: response }, 'updating user');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'updating user');
        }
    });
}

// Reset user password
function resetPassword(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    // Clear and show reset form
    $('#resetPasswordForm')[0].reset();
    $('#resetUserId').val(userId);
    $('#resetPasswordModal').modal('show');
}

// Reset user password
function resetUserPassword() {
    const userId = $('#resetUserId').val();
    const newPassword = $('#resetNewPassword').val();
    const forceChange = $('#forcePasswordChange').is(':checked');
    
    if (!newPassword) {
        showToast('Please enter a new password', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showToast('Password must be at least 6 characters long', 'error');
        return;
    }
    
    const formData = {
        new_password: newPassword,
        force_change: forceChange
    };
    
    $.ajax({
        url: `/api/user-profile/admin/user/${userId}/reset-password`,
        method: 'POST',
        data: JSON.stringify(formData),
        contentType: 'application/json',
        success: function(response) {
            if (response.success) {
                showToast('Password reset successfully', 'success');
                $('#resetPasswordModal').modal('hide');
                loadAllUsers(); // Refresh users list
            } else {
                handleApiError({ responseJSON: response }, 'resetting password');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'resetting password');
        }
    });
}

// Toggle user status
function toggleUserStatus(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) return;
    
    const action = user.is_active ? 'deactivate' : 'activate';
    const confirmMessage = `Are you sure you want to ${action} this user?`;
    
    if (!confirm(confirmMessage)) return;
    
    $.ajax({
        url: `/api/user-profile/admin/user/${userId}/toggle-status`,
        method: 'POST',
        success: function(response) {
            if (response.success) {
                showToast(response.message, 'success');
                loadAllUsers(); // Refresh users list
            } else {
                handleApiError({ responseJSON: response }, 'toggling user status');
            }
        },
        error: function(xhr, status, error) {
            handleApiError(xhr, 'toggling user status');
        }
    });
}

// Go back to main dashboard
function goBack() {
    window.location.href = '/';
}

// Handle tab changes
document.addEventListener('shown.bs.tab', function(event) {
    const targetTab = event.target.getAttribute('data-bs-target');
    
    if (targetTab === '#user-management' && currentUser && currentUser.role === 'admin') {
        loadAllUsers();
    }
});

// Real-time password strength validation
document.addEventListener('input', function(event) {
    if (event.target.id === 'newPassword' || event.target.id === 'resetNewPassword') {
        const password = event.target.value;
        const feedback = event.target.parentNode.querySelector('.password-feedback');
        
        if (feedback) {
            feedback.remove();
        }
        
        if (password.length > 0) {
            const strength = getPasswordStrength(password);
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = `form-text password-feedback text-${strength.color}`;
            feedbackDiv.innerHTML = `<i class="fas fa-${strength.icon} me-1"></i>${strength.message}`;
            event.target.parentNode.appendChild(feedbackDiv);
        }
    }
});

// Get password strength
function getPasswordStrength(password) {
    let score = 0;
    let feedback = [];
    
    // Length check
    if (password.length >= 6) score += 1;
    else feedback.push('at least 6 characters');
    
    // Letter check
    if (/[A-Za-z]/.test(password)) score += 1;
    else feedback.push('letters');
    
    // Number check
    if (/\d/.test(password)) score += 1;
    else feedback.push('numbers');
    
    // Special character check (bonus)
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
    
    if (score >= 3) {
        return {
            color: 'success',
            icon: 'check-circle',
            message: 'Strong password'
        };
    } else if (score >= 2) {
        return {
            color: 'warning',
            icon: 'exclamation-triangle',
            message: `Good password. Missing: ${feedback.join(', ')}`
        };
    } else {
        return {
            color: 'danger',
            icon: 'times-circle',
            message: `Weak password. Needs: ${feedback.join(', ')}`
        };
    }
}
