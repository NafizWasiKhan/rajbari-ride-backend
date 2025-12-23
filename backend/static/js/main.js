document.addEventListener('DOMContentLoaded', () => {
    console.log('App initialized');
    let currentUser = null;

    // --- Configuration & Helpers ---
    const map = L.map('map', {
        zoomControl: false, // Positioned manually or hidden for cleaner UI
        tap: true // Important for mobile touch
    }).setView([23.8103, 90.4125], 7);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Bounding box for Bangladesh
    const bangladeshBounds = {
        lat: [20.50, 26.50],
        lng: [88.00, 92.70]
    };
    // ===== STATE PERSISTENCE HELPER =====
    const RideState = {
        save(rideData) {
            try {
                localStorage.setItem('active_ride_state', JSON.stringify(rideData));
                console.log('[State] Saved ride state:', rideData.id);
            } catch (e) { console.error('[State] Save failed', e); }
        },
        load() {
            try {
                const data = localStorage.getItem('active_ride_state');
                return data ? JSON.parse(data) : null;
            } catch (e) {
                console.error('[State] Load failed', e);
                return null;
            }
        },
        clear() {
            localStorage.removeItem('active_ride_state');
            console.log('[State] Cleared ride state');
        }
    };
    // ===== END STATE PERSISTENCE =====


    function formatRideDate(dateStr) {
        if (!dateStr) return "Just now";
        try {
            const date = new Date(dateStr);
            if (isNaN(date)) return "Recently";
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + " " +
                date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) { return "Recently"; }
    }

    function formatAddressDisplay(addr) {
        if (!addr) return "Nearby";
        if (addr.startsWith('Loc:')) {
            // If it's still coordinates, make it slightly cleaner
            return addr.replace('Loc: ', '').split(',').map(n => parseFloat(n).toFixed(3)).join(', ');
        }
        return addr;
    }

    function setLoading(btnId, isLoading) {
        const btn = document.getElementById(btnId);
        if (!btn) return;
        if (isLoading) {
            btn.classList.add('loading');
            btn.disabled = true;
        } else {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    // --- Map Logic ---
    let pickupLatLng = null;
    let dropLatLng = null;
    let pickupAddress = null;
    let dropAddress = null;
    let pickupMarker = null;
    let dropMarker = null;
    let passengerMarker = null;
    let driverMarker = null;
    let routeLine = null;
    let routingControl = null; // New: To store the routing control instance

    // Draw Route Function (New)
    function drawRoute(pickup, drop) {
        if (routingControl) {
            map.removeControl(routingControl);
        }

        // Clear existing markers because Routing Machine adds its own, 
        // OR keep them and tell Routing Machine not to add markers.
        // Let's create a route line only, to avoid duplicate markers.

        routingControl = L.Routing.control({
            waypoints: [
                L.latLng(pickup.lat, pickup.lng),
                L.latLng(drop.lat, drop.lng)
            ],
            routeWhileDragging: false,
            draggableWaypoints: false,
            fitSelectedRoutes: true,
            show: false, // Hide the instructions panel
            addWaypoints: false,
            createMarker: function () { return null; }, // Don't create markers, we have our own
            lineOptions: {
                styles: [{ color: '#3498db', opacity: 0.8, weight: 6 }]
            }
        }).addTo(map);
    }

    // Locate Me
    const locateBtn = document.getElementById('locate-btn');
    locateBtn.onclick = () => {
        map.locate({ setView: true, maxZoom: 16 });
    };

    map.on('locationfound', (e) => {
        const radius = e.accuracy / 2;
        L.circle(e.latlng, radius).addTo(map);
    });

    map.on('locationerror', (e) => {
        alert("Location access denied or unavailable.");
    });

    window.resetSelection = function () {
        if (pickupMarker) map.removeLayer(pickupMarker);
        if (dropMarker) map.removeLayer(dropMarker);
        if (routeLine) map.removeLayer(routeLine); // Original routeLine clear
        if (routingControl) map.removeControl(routingControl); // Clear routingControl
        pickupLatLng = null; dropLatLng = null;
        pickupAddress = null; dropAddress = null;
        pickupMarker = null; dropMarker = null; routeLine = null;
        routingControl = null; // Reset routingControl

        document.getElementById('fare-display').style.display = "none";
        document.getElementById('address-summary').style.display = "none";
        document.getElementById('request-ride-btn').disabled = false;
        map.setView([23.8103, 90.4125], 7);
    };

    function updateAddressUI() {
        const summary = document.getElementById('address-summary');
        const pAddr = document.getElementById('sum-pickup-addr');
        const dAddr = document.getElementById('sum-drop-addr');
        const reqBtn = document.getElementById('request-ride-btn');

        if (pickupLatLng || dropLatLng) {
            summary.style.display = 'block';
            if (pAddr) pAddr.innerText = pickupAddress || "Finding address...";
            if (dAddr) dAddr.innerText = dropAddress || (pickupLatLng && dropLatLng ? "Finding address..." : "Selecting destination...");

            // Disable request button if addresses are still loading
            if ((pickupLatLng && !pickupAddress) || (dropLatLng && !dropAddress)) {
                reqBtn.disabled = true;
                reqBtn.innerText = "Finding Address...";
                reqBtn.style.opacity = "0.7";
            } else {
                reqBtn.disabled = false;
                reqBtn.innerText = "Request Ride";
                reqBtn.style.opacity = "1";
            }
        } else {
            summary.style.display = 'none';
            reqBtn.disabled = false;
            reqBtn.innerText = "Request Ride";
            reqBtn.style.opacity = "1";
        }
    }

    window.getFareEstimate = async function () {
        if (!pickupLatLng || !dropLatLng) return;

        // Draw Route (Road)
        drawRoute(pickupLatLng, dropLatLng);

        const token = localStorage.getItem('token');
        try {
            const response = await fetch('/api/rides/fare-estimate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`
                },
                body: JSON.stringify({
                    pickup_lat: pickupLatLng.lat,
                    pickup_lng: pickupLatLng.lng,
                    drop_lat: dropLatLng.lat,
                    drop_lng: dropLatLng.lng
                })
            });
            const data = await response.json();
            if (response.ok) {
                const fareEl = document.getElementById('fare-display');
                const costEl = document.getElementById('fare-amount');
                if (fareEl && costEl) {
                    costEl.innerText = data.estimated_fare;
                    fareEl.style.display = "block";
                }
            } else {
                alert("Error: " + (data.error || "Could not calculate fare"));
            }
        } catch (error) { // Fixed: matched variable name
            console.error(error);
        } finally {
            setLoading('request-ride-btn', false);
        }
    }

    // ... (rest of functions) ...

    // --- Generic Map Preview ---
    // Moved inside DOMContentLoaded or expose vars?
    // The issue is pickupMarker/dropMarker are defined inside DOMContentLoaded but previewRideOnMap is assigned to window.
    // Closures should work IF previewRideOnMap is defined INSIDE DOMContentLoaded.
    // It IS defined inside (line 1330 is inside the big arrow function starting at line 1).
    // So why is it undefined?
    // Ah, line 36: let pickupMarker = null; is defined.
    // The previous error `pickupMarker is not defined` might be because of a syntax error or scope issue I missed.
    // Let's look closer.
    // If I used `window.previewRideOnMap = ...` inside the closure, it SHOULD have access to `pickupMarker`.
    // UNLESS `pickupMarker` access is somehow shadowed or I messed up the braces in previous edits.
    // Let's re-verify the structure.

    // Actually, looking at the previous file content, `pickupMarker` is defined at line 36.
    // `previewRideOnMap` is at line 1330.
    // Both are inside `document.addEventListener('DOMContentLoaded', () => { ... });`.
    // Wait... if I assigned `window.previewRideOnMap` it becomes global.
    // The function BODY is defined inside scope, so it closes over `pickupMarker`.
    // So it should work.
    //
    // HOWEVER, if the previous edit accidentally closed the DOMContentLoaded callback EARLY, then `pickupMarker` would not be in scope for subsequent code.
    // Let's check where the `DOMContentLoaded` closes.
    // I see `});` at line 1218 in a previous view (when I viewed lines 1150-1300).
    // Wait, if `DOMContentLoaded` ends at 1218, then code after that (like `showMyRequests` at 1222) is OUTSIDE.
    // AND `pickupMarker` is INSIDE.
    // THIS IS THE BUG.
    // I need to move the closing brace of `DOMContentLoaded` to the very end of the file.

    // Plan:
    // 1. Remove the early `});` around line 1218 (or wherever it is).
    // 2. Add `});` at the very end of the file.
    //
    // Also fix the `catch(error)` issue at line 129.



    // Updated: Open Modal instead of direct request
    window.handleRideRequest = function () {
        if (!pickupLatLng || !dropLatLng) {
            alert("Please select both pickup and drop locations on the map.");
            return;
        }
        if (!localStorage.getItem('token')) {
            Auth.showModal('login');
            return;
        }

        // Populate Modal Details
        document.getElementById('req-pickup-addr').innerText = pickupAddress || `Loc: ${pickupLatLng.lat.toFixed(4)}, ${pickupLatLng.lng.toFixed(4)}`;
        document.getElementById('req-drop-addr').innerText = dropAddress || `Loc: ${dropLatLng.lat.toFixed(4)}, ${dropLatLng.lng.toFixed(4)}`;
        // Use the fare calculated earlier
        const fare = document.getElementById('fare-amount').innerText;
        document.getElementById('req-fare-display').innerText = fare + " BDT";

        document.getElementById('request-ride-modal').style.display = 'flex';
    };

    window.hideRequestModal = function () {
        document.getElementById('request-ride-modal').style.display = 'none';
    };

    window.confirmRideRequest = async function () {
        const token = localStorage.getItem('token');
        setLoading('request-ride-btn', true); // Loading on the main button or modal button? 
        // Let's add loading to the modal button actually, but for simplicity we reuse the global function logic style
        const btnCtx = event.target; // The confirm button
        const originalText = btnCtx.innerText;
        btnCtx.innerText = "Sending...";
        btnCtx.disabled = true;

        const vehicleType = document.querySelector('input[name="req-vehicle"]:checked').value;

        const statusDisplay = document.getElementById('ride-status-text');
        statusDisplay.innerText = "Requesting ride...";
        document.getElementById('status-container').style.display = "block";
        hideRequestModal();

        try {
            const body = {
                pickup_lat: pickupLatLng.lat,
                pickup_lng: pickupLatLng.lng,
                pickup_address: pickupAddress || `Loc: ${pickupLatLng.lat.toFixed(4)}, ${pickupLatLng.lng.toFixed(4)}`,
                drop_lat: dropLatLng.lat,
                drop_lng: dropLatLng.lng,
                drop_address: dropAddress || `Loc: ${dropLatLng.lat.toFixed(4)}, ${dropLatLng.lng.toFixed(4)}`
            };
            if (vehicleType) body.requested_vehicle_type = vehicleType;

            const url = editingRideId ? `/api/rides/${editingRideId}/update/` : '/api/rides/create/';
            const method = editingRideId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`
                },
                body: JSON.stringify(body)
            });

            const data = await response.json();
            if (response.ok) {
                if (editingRideId) {
                    alert("Ride request updated!");
                    editingRideId = null;
                    const reqBtn = document.getElementById('request-ride-btn');
                    reqBtn.innerText = "Request Ride";
                    reqBtn.style.background = "";
                    const cancelEditBtn = document.getElementById('cancel-edit-btn');
                    if (cancelEditBtn) cancelEditBtn.remove();

                    showMyRequests(); // Show the list
                    resetSelection();
                } else {
                    const rideId = data.id;
                    console.log("Ride created:", rideId);
                    statusDisplay.innerText = "Finding nearest driver...";
                    connectWebSocket(rideId, token, false);
                    startPassengerPolling(rideId); // Start polling fallback
                    document.getElementById('request-ride-btn').style.display = "none";
                }
            } else {
                alert("Request failed: " + (data.error || JSON.stringify(data)));
                document.getElementById('request-ride-btn').disabled = false;
            }
        } catch (error) {
            console.error(error);
            alert("Network Error");
        } finally {
            btnCtx.innerText = originalText;
            btnCtx.disabled = false;
            setLoading('request-ride-btn', false);
        }
    };

    // --- Polling Logic ---
    let driverPollInterval = null;
    let passengerPollInterval = null;
    let lastKnownRequestIds = new Set();

    function startDriverPolling() {
        stopDriverPolling();
        console.log("Starting driver polling...");
        driverPollInterval = setInterval(async () => {
            const token = localStorage.getItem('token');
            if (!token) return;
            try {
                const res = await fetch('/api/rides/available/', {
                    headers: { 'Authorization': `Token ${token}` }
                });
                if (res.ok) {
                    const rides = await res.json();
                    // Update badge count
                    const countEl = document.getElementById('available-count');
                    if (countEl) {
                        countEl.innerText = rides.length;
                        countEl.style.display = rides.length > 0 ? 'inline-block' : 'none';
                    }

                    // Check for new rides to notify
                    rides.forEach(ride => {
                        if (!lastKnownRequestIds.has(ride.id)) {
                            // New ride found!
                            handleNewRideRequest(ride);
                            lastKnownRequestIds.add(ride.id);
                        }
                    });

                    // If modal is open, refresh list
                    const availableRequestsModal = document.getElementById('available-requests-modal');
                    if (availableRequestsModal && availableRequestsModal.style.display === 'flex') {
                        showAvailableRequests();
                    }
                }
            } catch (e) { console.error("Driver poll error", e); }
        }, 5000); // Poll every 5 seconds
    }

    function stopDriverPolling() {
        if (driverPollInterval) clearInterval(driverPollInterval);
        driverPollInterval = null;
    }

    function startPassengerPolling(rideId) {
        if (passengerPollInterval) clearInterval(passengerPollInterval);
        console.log("Starting passenger polling for ride", rideId);

        passengerPollInterval = setInterval(async () => {
            const token = localStorage.getItem('token');
            try {
                const res = await fetch(`/api/rides/${rideId}/`, {
                    headers: { 'Authorization': `Token ${token}` }
                });
                if (res.ok) {
                    const ride = await res.json();
                    const activeStatuses = ['ASSIGNED', 'ONGOING', 'COMPLETED', 'PAID', 'FINISHED'];
                    if (activeStatuses.includes(ride.status)) {
                        updateRideStatus(ride.status, ride);

                        // Stop polling only when finished or cancelled
                        if (ride.status === 'FINISHED' || ride.status === 'CANCELLED') {
                            clearInterval(passengerPollInterval);
                        }
                    }
                }
            } catch (e) { console.error("Passenger poll error", e); }
        }, 5000);
    }

    // --- Role Management ---
    // --- Critical Initialization Helpers ---
    function stopJobPolling() {
        if (typeof chatInterval !== 'undefined') {
            clearInterval(chatInterval);
        }
    }

    let lastWalletHistory = [];

    async function fetchWalletStats() {
        const token = localStorage.getItem('token');
        if (!token || !currentUser) return;

        try {
            const res = await fetch('/api/payments/wallet/stats/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            const data = await res.json();
            if (res.ok) {
                lastWalletHistory = data.history || [];

                // Update Driver UI
                const incomeEl = document.getElementById('stats-total-income');
                const balanceEl = document.getElementById('stats-wallet-balance');
                if (incomeEl) incomeEl.innerText = data.total_earnings.toFixed(2) + ' BDT';
                if (balanceEl) balanceEl.innerText = data.balance.toFixed(2) + ' BDT';

                // Update Passenger UI
                const passengerCard = document.getElementById('passenger-stats-card');
                const spentEl = document.getElementById('p-stats-spent');
                const countEl = document.getElementById('p-stats-count');

                if (currentUser.profile.role === 'PASSENGER') {
                    if (passengerCard) passengerCard.style.display = 'block';
                    if (spentEl) spentEl.innerText = data.total_spent.toFixed(2) + ' BDT';
                    if (countEl) {
                        // We can derive trip count from history types if needed, or backend can provide it.
                        // For now let's just use the history length or a specific key if we added it.
                        countEl.innerText = data.history.filter(t => t.type === 'RIDE_PAYMENT').length;
                    }
                } else {
                    if (passengerCard) passengerCard.style.display = 'none';
                }
            }
        } catch (e) { console.error("Wallet stats fail", e); }
    }

    window.showTransactionsModal = () => {
        const modal = document.getElementById('transactions-modal');
        const list = document.getElementById('transactions-list');
        modal.style.display = 'flex';

        if (lastWalletHistory.length === 0) {
            list.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No recent activities found.</p>';
            return;
        }

        list.innerHTML = lastWalletHistory.map(t => {
            const isEarn = ['EARNING', 'TOPUP'].includes(t.type);
            const color = isEarn ? '#27ae60' : '#e74c3c';
            const icon = isEarn ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';

            return `
                <div style="background: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; border-left: 4px solid ${color}; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                    <div style="flex: 1;">
                        <p style="margin: 0; font-weight: 700; font-size: 14px; color: #333;">${t.description || t.type}</p>
                        <p style="margin: 2px 0 0 0; font-size: 11px; color: #999;">${new Date(t.timestamp).toLocaleString()}</p>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin: 0; font-weight: 800; color: ${color}; font-size: 15px;">
                            ${isEarn ? '+' : '-'}${Math.abs(t.amount).toFixed(2)}
                        </p>
                        <i class="fas ${icon}" style="font-size: 10px; color: ${color}; opacity: 0.5;"></i>
                    </div>
                </div>
            `;
        }).join('');
    };

    window.hideTransactionsModal = () => document.getElementById('transactions-modal').style.display = 'none';

    async function initDashboard() {
        const role = localStorage.getItem('userRole');
        const token = localStorage.getItem('token');

        const passengerUI = document.getElementById('passenger-dashboard');
        const driverUI = document.getElementById('driver-dashboard');
        const onlineBtn = document.getElementById('online-toggle-btn');
        const statusText = document.getElementById('availability-status');

        if (token) {
            try {
                const res = await fetch('/api/users/profile/', {
                    headers: { 'Authorization': `Token ${token}` }
                });
                const userData = await res.json();
                const profile = userData.user.profile;
                currentUser = userData.user; // Set in closure scope
                window.currentUser = currentUser; // Also set globally for legacy compatibility

                if (onlineBtn && profile.role === 'DRIVER') {
                    const isOnline = profile.is_online;
                    onlineBtn.style.background = isOnline ? '#2ecc71' : '#e74c3c';
                    if (statusText) {
                        statusText.innerText = isOnline ? 'Online' : 'Offline';
                        statusText.style.color = isOnline ? '#2ecc71' : '#e74c3c';
                    }
                    const badge = document.getElementById('availability-status-badge');
                    if (badge) {
                        badge.innerText = isOnline ? 'Online' : 'Offline';
                        badge.style.background = isOnline ? '#2ecc71' : '#e74c3c';
                    }
                    const jobText = document.getElementById('job-status-text');
                    if (jobText && isOnline && jobText.innerText.includes("Go online")) {
                        jobText.innerHTML = '<i class="fas fa-search-location"></i> Searching for nearby ride requests...';
                    }
                }
            } catch (e) { console.error("Profile fetch failed", e); }
        }

        if (token && role === 'DRIVER') {
            if (passengerUI) passengerUI.style.display = 'none';
            if (driverUI) driverUI.style.display = 'block';
            if (onlineBtn) onlineBtn.style.display = 'flex';

            if (currentUser && !notificationSocket) {
                if (typeof connectNotificationSocket === 'function') connectNotificationSocket();
            }
            fetchWalletStats();
            updateAvailableCount();
        } else {
            if (passengerUI) passengerUI.style.display = 'block';
            if (driverUI) driverUI.style.display = 'none';
            if (onlineBtn) onlineBtn.style.display = 'none';
            stopJobPolling();
            stopDriverPolling();
            fetchWalletStats();
        }

        const scheduleControls = document.getElementById('driver-schedule-controls');
        if (scheduleControls) {
            scheduleControls.style.display = token ? 'block' : 'none';
        }

        // Restore view if saved
        const lastView = localStorage.getItem('currentView');
        if (lastView === 'SCHEDULED_RIDES') {
            window.showScheduledRides();
        } else if (lastView === 'AVAILABLE_REQUESTS') {
            window.showAvailableRequests();
        }

        if (token) {
            checkActiveRide();
        }
    }

    async function checkActiveRide() {
        const token = localStorage.getItem('token');
        const role = localStorage.getItem('userRole');

        if (!token) {
            console.log('[Recovery] No token, skipping active ride check');
            return;
        }

        // First check localStorage for cached state (instant UI restore)
        const cachedState = RideState.load();
        if (cachedState) {
            console.log("[Recovery] Restoring from cache:", cachedState.id, cachedState.status);
            updateRideStatus(cachedState.status, cachedState);
        }

        // Then fetch fresh data from server
        try {
            const res = await fetch('/api/rides/current/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            if (res.ok) {
                const ride = await res.json();
                console.log("[Recovery] Active ride found:", ride.id, ride.status);

                // Save to cache for next reload
                RideState.save(ride);

                // Update UI with fresh data
                updateRideStatus(ride.status, ride);

                // Reconnect WebSocket (will fallback to polling if WS fails)
                if (typeof connectWebSocket === 'function') {
                    connectWebSocket(ride.id, token, role === 'DRIVER');
                }

                // Start polling for driver
                if (role === 'DRIVER' && currentUser?.profile?.is_online) {
                    startDriverPolling();
                }

                // Start polling for passenger
                if (role === 'PASSENGER' && ['REQUESTED', 'ASSIGNED', 'ONGOING'].includes(ride.status)) {
                    startPassengerPolling(ride.id);
                }
            } else {
                // No active ride on server, clear cache
                console.log("[Recovery] No active ride on server, clearing cache");
                RideState.clear();
            }
        } catch (e) {
            console.log("[Recovery] Error fetching active ride (likely no internet):", e.message);
            // If network error but cache exists, keep using cache
            if (cachedState) {
                console.log("[Recovery] Using cached state due to network error");
            }
        }
    }

    window.toggleOnlineStatus = async function () {
        const token = localStorage.getItem('token');
        const btn = document.getElementById('online-toggle-btn');
        const statusText = document.getElementById('availability-status');

        setLoading('online-toggle-btn', true);
        try {
            const response = await fetch('/api/users/profile/toggle-online/', {
                method: 'PATCH',
                headers: { 'Authorization': `Token ${token}` }
            });
            const data = await response.json();
            if (response.ok) {
                const isOnline = data.is_online;
                if (btn) btn.style.background = isOnline ? '#2ecc71' : '#e74c3c';

                if (statusText) {
                    statusText.innerText = isOnline ? 'Online' : 'Offline';
                    statusText.style.color = isOnline ? '#2ecc71' : '#e74c3c';
                }

                // Update global currentUser state and trigger UI refreshing
                if (currentUser) currentUser.profile.is_online = isOnline;

                const badge = document.getElementById('availability-status-badge');
                if (badge) {
                    badge.innerText = isOnline ? 'Online' : 'Offline';
                    badge.style.background = isOnline ? '#2ecc71' : '#e74c3c';
                }

                const jobText = document.getElementById('job-status-text');
                if (jobText) {
                    if (isOnline) {
                        jobText.innerHTML = '<i class="fas fa-search-location"></i> Searching for nearby ride requests...';
                        updateAvailableCount();
                        startDriverPolling(); // Start polling when online
                    } else {
                        jobText.innerText = "Go online to see ride requests from passengers.";
                        const acceptBtn = document.getElementById('job-accept-btn');
                        if (acceptBtn) acceptBtn.style.display = 'none';
                        stopDriverPolling(); // Stop polling when offline
                    }
                }

                initDashboard();
            }
        } finally {
            setLoading('online-toggle-btn', false);
        }
    };

    if (document.getElementById('online-toggle-btn')) {
        document.getElementById('online-toggle-btn').onclick = () => toggleOnlineStatus();
    }

    initDashboard();

    function updateRideStatus(status, details = {}) {
        const text = document.getElementById('ride-status-text');
        const driverInfo = document.getElementById('driver-info');
        const statusContainer = document.getElementById('status-container');
        const finishTripBtn = document.getElementById('finish-trip-btn');
        const payNowBtn = document.getElementById('pay-now-btn');
        const requestRideBtn = document.getElementById('request-ride-btn');
        const jobStatusText = document.getElementById('job-status-text');
        const jobActiveControls = document.getElementById('job-active-controls');
        const dynamicGrid = document.getElementById('passenger-dynamic-grid');

        // Robust role detection
        const storedRole = localStorage.getItem('userRole');
        const isDriver = storedRole === 'DRIVER' || (currentUser && currentUser.profile && currentUser.profile.role === 'DRIVER');

        // Force hide request button if any active ride status exists
        const isActive = ['ASSIGNED', 'ONGOING', 'COMPLETED', 'PAID'].includes(status);
        if (isActive && requestRideBtn) {
            requestRideBtn.style.display = 'none';

            // Save state for persistence across reloads
            if (details && details.id) {
                const stateData = { ...details, status: status };
                RideState.save(stateData);
            }
        }

        if (isActive && statusContainer) {
            statusContainer.style.display = 'block';
        }

        // Hide special buttons by default
        if (finishTripBtn) finishTripBtn.style.display = 'none';
        if (payNowBtn) payNowBtn.style.display = 'none';
        const confirmBtn = document.getElementById('job-confirm-finish-btn');
        if (confirmBtn) confirmBtn.style.display = 'none';

        if (status === 'ASSIGNED' || status === 'ONGOING') {
            if (isDriver) {
                if (jobStatusText) {
                    jobStatusText.innerHTML = status === 'ASSIGNED' ?
                        '<i class="fas fa-car-side"></i> Navigate to pickup location.' :
                        '<i class="fas fa-route"></i> Trip in progress. Navigate to destination.';
                }
                if (jobActiveControls) jobActiveControls.style.display = 'flex';

                const chatBtn = document.getElementById('job-chat-btn');
                const finishBtn = document.getElementById('job-finish-btn');

                const riderId = details.rider || details.rider_id;
                const rideId = details.id || details.ride_id;
                const riderName = details.rider_username || 'Rider';

                if (chatBtn && rideId && riderId) {
                    console.log("[Chat] Binding Driver Chat:", rideId, riderId);
                    chatBtn.onclick = () => openChat(rideId, riderId, riderName);
                } else if (chatBtn) {
                    console.warn("[Chat] Driver Chat binding failed: missing IDs", { rideId, riderId });
                }

                if (finishBtn && rideId) {
                    finishBtn.onclick = () => finishRide(rideId);
                }
            } else {
                if (text) text.innerText = status === 'ASSIGNED' ? "Driver is on the way!" : "Ride in progress...";
                if (driverInfo) driverInfo.style.display = "block";
                if (finishTripBtn) finishTripBtn.style.display = "block";
                if (requestRideBtn) requestRideBtn.style.display = 'none';

                // Setup Chat & Call for Passenger
                const chatBtn = document.getElementById('chat-with-driver-btn');
                const dId = details.driver || details.driver_id;
                const rideId = details.id || details.ride_id;

                if (chatBtn && rideId && dId) {
                    chatBtn.style.display = 'flex';
                    chatBtn.onclick = () => openChat(rideId, dId, details.driver_name || 'Driver');
                }
            }

            // Sync maps and markers (mostly for Passenger)
            if (!isDriver && details.lat && details.lng) {
                updateDriverMarker(details.lat, details.lng);
            }

            // Draw route if missing
            if (details.pickup_lat && details.drop_lat) {
                const p = { lat: parseFloat(details.pickup_lat), lng: parseFloat(details.pickup_lng) };
                const d = { lat: parseFloat(details.drop_lat), lng: parseFloat(details.drop_lng) };
                if (!pickupMarker) {
                    pickupMarker = L.marker(p, { icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-circle-dot" style="color:black"></i>', iconAnchor: [12, 12] }) }).addTo(map);
                    dropMarker = L.marker(d, { icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-location-pin" style="color:black"></i>', iconAnchor: [12, 12] }) }).addTo(map);
                    drawRoute(p, d);
                }
            }

        } else if (status === 'COMPLETED') {
            if (isDriver) {
                if (jobStatusText) jobStatusText.innerText = "Trip Completed. Waiting for payment.";
                if (jobActiveControls) jobActiveControls.style.display = 'flex';
            } else {
                if (text) text.innerText = "Arrived! Please pay the fare.";
                if (payNowBtn) payNowBtn.style.display = "block";
                if (finishTripBtn) finishTripBtn.style.display = 'none';
            }
            // Do NOT cleanup here, we need to wait for payment confirmation
        } else if (status === 'PAID') {
            const isDriver = currentUser && currentUser.profile.role === 'DRIVER';

            if (isDriver) {
                text.innerText = "Payment Received! Please verify and close.";
                if (jobStatusText) {
                    const amountMsg = details.amount_paid ? ` ${details.amount_paid} BDT` : '';
                    jobStatusText.innerHTML = `<div style="color: #27ae60; font-weight: 800;"><i class="fas fa-check-circle"></i> Passenger Paid${amountMsg}! Confirm to close ride.</div>`;
                }
                const confirmBtn = document.getElementById('job-confirm-finish-btn');
                const finishBtn = document.getElementById('job-finish-btn');
                if (confirmBtn) {
                    confirmBtn.style.display = 'block';
                    let safeRideId = details.id || details.ride_id;

                    // Fallback to global if available
                    if (!safeRideId && typeof currentChatRideId !== 'undefined' && currentChatRideId) {
                        safeRideId = currentChatRideId;
                    }

                    if (!safeRideId) {
                        console.error("Critical: Missing Ride ID in PAID status update", details);
                        alert("Error: Ride ID missing. Please refresh. (Debug: " + JSON.stringify(details) + ")");
                    } else {
                        console.log("Binding confirmFinishRide with ID:", safeRideId);
                        confirmBtn.onclick = () => confirmFinishRide(safeRideId);
                    }
                }
                if (finishBtn) finishBtn.style.display = 'none';
            } else {
                text.innerText = "Payment Sent! Waiting for driver to confirm receipt...";
                if (payNowBtn) payNowBtn.style.display = "none";
                if (finishTripBtn) finishTripBtn.style.display = 'none';
            }
            // Do NOT cleanup yet! We stay in PAID until driver confirms.

        } else if (status === 'FINISHED') {
            if (text) text.innerText = "Ride Finished! Thank you.";
            if (payNowBtn) payNowBtn.style.display = "none";
            if (requestRideBtn) requestRideBtn.style.display = 'block';
            if (driverInfo) driverInfo.style.display = 'none';
            if (jobActiveControls) jobActiveControls.style.display = 'none';

            // Hide the active status container to show main dashboard
            if (statusContainer) {
                setTimeout(() => {
                    statusContainer.style.display = 'none';
                    if (text) text.innerText = 'Where to go?';
                }, 3000);
            }

            RideState.clear();
            cleanupLiveTracking();
            setTimeout(resetSelection, 3000);

        } else if (status === 'CANCELLED') {
            text.innerText = "Ride has been cancelled.";
            if (requestRideBtn) requestRideBtn.style.display = 'block';
            if (driverInfo) driverInfo.style.display = 'none';
            cleanupLiveTracking();
        }

        // Adjust passenger grid layout
        if (dynamicGrid) {
            const isFinishVisible = finishTripBtn && finishTripBtn.style.display !== 'none';
            const isPayVisible = payNowBtn && payNowBtn.style.display !== 'none';
            if (isFinishVisible || isPayVisible) {
                dynamicGrid.style.gridTemplateColumns = '1fr 1fr';
            } else {
                dynamicGrid.style.gridTemplateColumns = '1fr';
            }
        }
    }

    function cleanupLiveTracking() {
        stopSendingLocation();
        if (driverMarker) { map.removeLayer(driverMarker); driverMarker = null; }
        if (passengerMarker) { map.removeLayer(passengerMarker); passengerMarker = null; }
    }

    // --- Scheduled Rides Flow ---
    window.showScheduledRides = async function () {
        localStorage.setItem('currentView', 'SCHEDULED_RIDES');
        document.getElementById('passenger-dashboard').style.display = 'none';
        document.getElementById('driver-dashboard').style.display = 'none';
        document.getElementById('scheduled-rides-dashboard').style.display = 'block';

        const listContainer = document.getElementById('scheduled-rides-list');
        listContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Loading rides...</p>';

        try {
            const response = await fetch('/api/rides/scheduled/list/');
            const rides = await response.json();

            if (rides.length === 0) {
                listContainer.innerHTML = '<p style="text-align: center; padding: 20px; color: #888;">No scheduled rides available.</p>';
                return;
            }

            listContainer.innerHTML = rides.map(ride => {
                const isOffer = ride.ride_type === 'OFFER' || !!ride.driver;
                const creator = isOffer ? ride.driver_username : ride.rider_username;
                const badgeColor = isOffer ? '#2ecc71' : '#3498db';
                const badgeText = isOffer ? 'DRIVER OFFER' : 'PASSENGER REQUEST';
                const otherUserId = ride.driver || ride.rider;

                return `
                    <div style="background: white; padding: 16px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                            <span style="font-size: 10px; font-weight: 800; color: white; background: ${badgeColor}; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">${badgeText}</span>
                            <span style="font-weight: 700; color: #2ecc71;">${ride.estimated_fare} BDT</span>
                        </div>
                        <p style="font-size: 13px; font-weight: 600; margin-bottom: 4px;">Posted by: ${creator}</p>
                        <p style="font-size: 14px; color: #666; margin-bottom: 4px;">🚀 Leaves: ${new Date(ride.scheduled_datetime).toLocaleString()}</p>
                        <p style="font-size: 12px; color: #444; margin-bottom: 2px;">📍 <strong>From:</strong> ${ride.pickup_address || 'Current'}</p>
                        <p style="font-size: 12px; color: #444; margin-bottom: 12px;">🏁 <strong>To:</strong> ${ride.drop_address || 'Destination'}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 12px; color: #888;">${ride.available_seats} Seats Left</span>
                            ${(ride.rider === currentUser.id || ride.driver === currentUser.id) ?
                        `<button class="btn btn-secondary btn-sm" onclick="showRideRequests(${ride.id})" style="padding: 6px 12px; font-size: 12px; width: auto; background: #34495e;">Manage</button>` :
                        (ride.user_request_status ?
                            `<div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                                <span style="font-size: 11px; padding: 4px 8px; background: #f39c12; color: white; border-radius: 4px; font-weight: bold;">${ride.user_request_status}</span>
                                ${ride.user_request_status === 'APPROVED' && ride.creator_phone ?
                                `<div style="display: flex; gap: 8px;">
                                        <a href="tel:${ride.creator_phone}" class="btn btn-primary btn-sm" style="background: #27ae60; font-size: 11px; padding: 4px 8px; width: auto;">
                                            <i class="fas fa-phone"></i> Call
                                        </a>
                                        <button class="btn btn-primary btn-sm" onclick="openChat(${ride.id}, ${otherUserId}, '${creator}')" style="background: #3498db; font-size: 11px; padding: 4px 8px; width: auto;">
                                            <i class="fas fa-comment"></i> Chat
                                        </button>
                                        <a href="https://wa.me/${ride.creator_phone}" target="_blank" class="btn btn-primary btn-sm" style="background: #25D366; font-size: 11px; padding: 4px 8px; width: auto;">
                                            <i class="fab fa-whatsapp"></i> WA
                                        </a>
                                    </div>` : ''
                            }
                            </div>` :
                            `<button class="btn btn-primary btn-sm" onclick="requestSeat(${ride.id}, ${ride.available_seats})" style="padding: 6px 12px; font-size: 12px; width: auto;">Join Ride</button>`
                        )
                    }
                        </div>
                    </div>
                `;
            }).join('');
        } catch (error) {
            listContainer.innerHTML = '<p style="color: red; text-align: center;">Failed to load rides.</p>';
        }
    };

    window.showRideRequests = async function (rideId) {
        const modal = document.getElementById('requests-modal');
        const list = document.getElementById('requests-list');
        const token = localStorage.getItem('token');

        modal.style.display = 'flex';
        list.innerHTML = '<p style="text-align: center;">Loading requests...</p>';

        try {
            // We'll need a way to filter requests by ride. 
            // For now, let's fetch all 'My Requests' and filter locally for simplicity, 
            // or better, implement a backend filter.
            // Actually, HandleSeatRequestView exists but we need to SEE the requests first.
            // I'll assume we need an endpoint to see requests FOR a ride.
            const response = await fetch(`/api/rides/scheduled/my-requests/?ride_id=${rideId}`, {
                headers: { 'Authorization': `Token ${token}` }
            });
            const requests = await response.json();

            if (requests.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: #888;">No pending requests.</p>';
                return;
            }

            list.innerHTML = requests.map(req => `
                <div style="border-bottom: 1px solid #eee; padding: 12px 0;">
                    <p style="font-weight: 600;">${req.passenger_username} (${req.seats_requested} seats)</p>
                    ${req.passenger_phone ? `
                        <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                            <a href="tel:${req.passenger_phone}" style="font-size: 12px; color: #27ae60; text-decoration: none;">
                                <i class="fas fa-phone"></i> ${req.passenger_phone}
                            </a>
                            <a href="https://wa.me/${req.passenger_phone}" target="_blank" style="font-size: 12px; color: #25D366; text-decoration: none;">
                                <i class="fab fa-whatsapp"></i> Chat
                            </a>
                            <button class="btn btn-primary btn-sm" onclick="openChat(${req.ride}, ${req.passenger}, '${req.passenger_username}')" style="background: #3498db; font-size: 10px; padding: 2px 6px; width: auto; height: auto;">
                                <i class="fas fa-comment"></i> App Chat
                            </button>
                        </div>` : ''}
                    <p style="font-size: 12px; color: #888; margin-bottom: 8px;">Status: ${req.status}</p>
                    ${req.status === 'PENDING' ? `
                        <div style="display: flex; gap: 8px;">
                            <button class="btn btn-primary btn-sm" onclick="handleRequestAction(${req.id}, 'APPROVE')" style="padding: 4px 8px; font-size: 11px;">Approve</button>
                            <button class="btn btn-secondary btn-sm" onclick="handleRequestAction(${req.id}, 'REJECT')" style="padding: 4px 8px; font-size: 11px; background: #e74c3c;">Reject</button>
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } catch (e) { list.innerHTML = 'Error loading requests'; }
    };

    window.hideRequestsModal = () => document.getElementById('requests-modal').style.display = 'none';

    window.handleRequestAction = async function (reqId, action) {
        const token = localStorage.getItem('token');
        try {
            const response = await fetch(`/api/rides/scheduled/handle-request/${reqId}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify({ action })
            });
            if (response.ok) {
                alert(`Request ${action === 'APPROVE' ? 'Approved' : 'Rejected'}`);
                hideRequestsModal();
                showScheduledRides();
            } else {
                const unta = await response.json();
                alert(unta.error || "Action failed");
            }
        } catch (e) {
            console.error("Approval action failed", e);
            alert("Network error: " + e.message);
        }
    };

    window.backToDashboard = function () {
        localStorage.removeItem('currentView');
        document.getElementById('scheduled-rides-dashboard').style.display = 'none';
        initDashboard();
    };

    window.showCreateScheduleModal = function () {
        if (!pickupLatLng || !dropLatLng) {
            alert("Please select pickup and drop on the map first!");
            return;
        }
        document.getElementById('create-schedule-modal').style.display = 'flex';
    };

    window.hideCreateScheduleModal = function () {
        document.getElementById('create-schedule-modal').style.display = 'none';
    };

    window.submitScheduledRide = async function () {
        const time = document.getElementById('sched-time').value;
        const seats = document.getElementById('sched-seats').value;
        const token = localStorage.getItem('token');

        if (!time) return alert("Select a time");

        try {
            const response = await fetch('/api/rides/scheduled/create/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify({
                    pickup_lat: pickupLatLng.lat, pickup_lng: pickupLatLng.lng,
                    pickup_address: pickupAddress || `Loc: ${pickupLatLng.lat.toFixed(4)}, ${pickupLatLng.lng.toFixed(4)}`,
                    drop_lat: dropLatLng.lat, drop_lng: dropLatLng.lng,
                    drop_address: dropAddress || `Loc: ${dropLatLng.lat.toFixed(4)}, ${dropLatLng.lng.toFixed(4)}`,
                    scheduled_datetime: time, available_seats: seats
                })
            });
            if (response.ok) {
                alert("Scheduled ride posted!");
                hideCreateScheduleModal();
                resetSelection();
            } else {
                const data = await response.json();
                alert(JSON.stringify(data));
            }
        } catch (e) { alert("Error creating ride"); }
    };

    window.requestSeat = function (rideId, maxSeats) {
        if (!localStorage.getItem('token')) {
            Auth.showModal('login');
            return;
        }

        const modal = document.getElementById('join-confirmation-modal');
        const seatsInput = document.getElementById('seats-to-request');
        const confirmBtn = document.getElementById('confirm-join-btn');

        modal.style.display = 'flex';
        seatsInput.max = maxSeats;
        seatsInput.value = 1;

        confirmBtn.onclick = async () => {
            const seats = seatsInput.value;
            setLoading('confirm-join-btn', true);
            try {
                const response = await fetch('/api/rides/scheduled/request-seat/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({ ride: rideId, seats_requested: parseInt(seats) })
                });

                if (response.ok) {
                    alert("Join request sent! Wait for creator's approval.");
                    hideJoinModal();
                    showScheduledRides();
                } else {
                    const data = await response.json();
                    alert(data.non_field_errors || "Request failed");
                }
            } catch (error) {
                console.error(error);
                alert("Network error.");
            } finally {
                setLoading('confirm-join-btn', false);
            }
        };
    };

    window.hideJoinModal = () => document.getElementById('join-confirmation-modal').style.display = 'none';

    async function reverseGeocode(lat, lng, type) {
        if (type === 'pickup') pickupAddress = null;
        else dropAddress = null;
        updateAddressUI();

        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`);
            const data = await response.json();
            if (data && data.display_name) {
                const clean = data.display_name.split(',').slice(0, 3).join(',');
                if (type === 'pickup') pickupAddress = clean;
                else dropAddress = clean;
            } else {
                if (type === 'pickup') pickupAddress = `Loc: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
                else dropAddress = `Loc: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            }
        } catch (e) {
            console.warn("Reverse geocode failed", e);
            if (type === 'pickup') pickupAddress = `Loc: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            else dropAddress = `Loc: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        }
        updateAddressUI();
    }

    map.on('click', async (e) => {
        const { lat, lng } = e.latlng;
        // Basic boundary check for Bangladesh
        if (lat >= bangladeshBounds.lat[0] && lat <= bangladeshBounds.lat[1] &&
            lng >= bangladeshBounds.lng[0] && lng <= bangladeshBounds.lng[1]) {

            if (!pickupLatLng) {
                pickupLatLng = e.latlng;
                pickupMarker = L.marker(pickupLatLng, {
                    icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-circle-dot" style="color:black"></i>', iconAnchor: [12, 12] })
                }).addTo(map);
                await reverseGeocode(lat, lng, 'pickup');
            } else if (!dropLatLng) {
                dropLatLng = e.latlng;
                dropMarker = L.marker(dropLatLng, {
                    icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-location-pin" style="color:black"></i>', iconAnchor: [12, 12] })
                }).addTo(map);
                await reverseGeocode(lat, lng, 'drop');
                getFareEstimate();
            }
        } else {
            alert("We only serve within Bangladesh area for now.");
        }
    });

    // --- WebSocket & Payments (Kept from original) ---
    let rideSocket = null;
    let gpsInterval = null;

    window.connectWebSocket = function (rideId, token, isDriver) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/rides/${rideId}/?token=${token}`;

        console.log(`[Socket] Connecting to Ride ${rideId}...`);
        rideSocket = new WebSocket(wsUrl);

        rideSocket.onopen = () => {
            console.log("[Socket] Connected! Initializing live location...");
            startSendingLocation();
        };

        rideSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'location_update') {
                // Determine whose location this is
                if (data.role === 'DRIVER' && !isDriver) {
                    updateDriverMarker(data.lat, data.lng);
                } else if (data.role === 'PASSENGER' && isDriver) {
                    updatePassengerMarker(data.lat, data.lng);
                }
            } else if (data.type === 'status_update') {
                updateRideStatus(data.status, data);
            }
        };

        rideSocket.onclose = () => {
            console.log("[Socket] Disconnected.");
            stopSendingLocation();
        };
    };

    function startSendingLocation() {
        if (!navigator.geolocation) {
            console.warn("Geolocation not supported by this browser.");
            return;
        }

        stopSendingLocation(); // Clear any existing

        const badge = document.getElementById('live-location-badge');
        const controls = document.getElementById('live-location-controls');
        if (badge) badge.style.display = 'flex';
        if (controls) controls.style.display = 'block';

        console.log("[GPS] Starting high-accuracy tracking...");
        gpsInterval = setInterval(() => {
            navigator.geolocation.getCurrentPosition((pos) => {
                if (rideSocket?.readyState === WebSocket.OPEN) {
                    rideSocket.send(JSON.stringify({
                        'type': 'location_update',
                        'lat': pos.coords.latitude,
                        'lng': pos.coords.longitude
                    }));
                }
            }, (err) => {
                console.error("[GPS] Error:", err.message);
                if (badge) {
                    const status = document.getElementById('location-sharing-status');
                    if (status) status.innerText = "GPS ERROR: " + err.message;
                    badge.style.background = "rgba(231, 76, 60, 0.1)";
                    badge.style.color = "#e74c3c";
                    badge.style.borderColor = "rgba(231, 76, 60, 0.2)";
                }
            }, { enableHighAccuracy: true });
        }, 5000);
    }

    function stopSendingLocation() {
        if (gpsInterval) {
            clearInterval(gpsInterval);
            gpsInterval = null;
        }
        const badge = document.getElementById('live-location-badge');
        const controls = document.getElementById('live-location-controls');
        if (badge) badge.style.display = 'none';
        if (controls) controls.style.display = 'none';

        // Reset colors if they were changed due to error
        if (badge) {
            badge.style.background = "rgba(46, 204, 113, 0.1)";
            badge.style.color = "#2ecc71";
            badge.style.borderColor = "rgba(46, 204, 113, 0.2)";
            const status = document.getElementById('location-sharing-status');
            if (status) status.innerText = "SHARING ACTIVE";
        }
    }

    window.toggleLocationSharing = function () {
        const btn = document.getElementById('toggle-location-btn');
        if (gpsInterval) {
            stopSendingLocation();

            // Re-show controls but with "Start" text
            const controls = document.getElementById('live-location-controls');
            if (controls) controls.style.display = 'block';
            if (btn) btn.innerHTML = '<i class="fas fa-location-arrow"></i> START SHARING';
            alert("Live location sharing paused.");
        } else {
            startSendingLocation();
            if (btn) btn.innerHTML = '<i class="fas fa-location-arrow"></i> STOP SHARING';
        }
    };

    function updatePassengerMarker(lat, lng) {
        const icon = L.divIcon({
            className: 'custom-icon',
            html: '<i class="fas fa-user-circle" style="color:#2ecc71; font-size: 32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));"></i>',
            iconAnchor: [16, 16]
        });
        if (passengerMarker) {
            passengerMarker.setLatLng([lat, lng]);
        } else {
            passengerMarker = L.marker([lat, lng], { icon }).addTo(map);
            // Optionally auto-pan if driver is looking for passenger
            // map.panTo([lat, lng]);
        }
    }

    function updateDriverMarker(lat, lng) {
        const icon = L.divIcon({
            className: 'custom-icon',
            html: '<i class="fas fa-car" style="color:#000; font-size:32px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));"></i>',
            iconAnchor: [16, 16]
        });
        if (driverMarker) {
            driverMarker.setLatLng([lat, lng]);
        } else {
            driverMarker = L.marker([lat, lng], { icon }).addTo(map);
        }
    }

    function cleanupLiveTracking() {
        console.log("[Cleanup] Tearing down live tracking and map overlays...");
        stopSendingLocation();
        if (rideSocket) {
            rideSocket.close();
            rideSocket = null;
        }
        if (pickupMarker) { map.removeLayer(pickupMarker); pickupMarker = null; }
        if (dropMarker) { map.removeLayer(dropMarker); dropMarker = null; }
        if (driverMarker) { map.removeLayer(driverMarker); driverMarker = null; }
        if (passengerMarker) { map.removeLayer(passengerMarker); passengerMarker = null; }
        if (routeLine) { map.removeLayer(routeLine); routeLine = null; }
        if (routingControl) { map.removeControl(routingControl); routingControl = null; }
    }

    window.handleFinishRide = async function () {
        const token = localStorage.getItem('token');
        try {
            const res = await fetch('/api/rides/current/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            if (res.ok) {
                const ride = await res.json();
                finishRide(ride.id);
            }
        } catch (e) { console.error(e); }
    }

    window.showPaymentMethodModal = () => document.getElementById('payment-method-modal').style.display = 'flex';
    window.hidePaymentMethodModal = () => document.getElementById('payment-method-modal').style.display = 'none';

    window.selectPaymentMethod = async function (method) {
        // If Cash is selected, show input and hide options
        if (method === 'CASH') {
            const inputContainer = document.getElementById('cash-amount-container');
            const optionsContainer = document.querySelector('#payment-method-modal .modal-card > div:nth-child(3)'); // The grid container

            if (inputContainer && optionsContainer) {
                inputContainer.style.display = 'block';
                // Highlight we are in cash mode or hide others? Let's just show the input below.
                // Or better, hide the grid to focus on input.
                // optionsContainer.style.display = 'none'; 
            }
            return;
        }

        // For Digital, proceed as usual
        initiatePaymentRequest(method, null);
    };

    window.confirmCashPayment = async function () {
        const amountInput = document.getElementById('cash-amount-input');
        const amount = parseFloat(amountInput.value);

        if (!amount || amount <= 0) {
            alert("Please enter a valid amount.");
            return;
        }

        initiatePaymentRequest('CASH', amount);
    };

    async function initiatePaymentRequest(method, amount) {
        hidePaymentMethodModal();
        const token = localStorage.getItem('token');
        let rideId = null;

        try {
            const res = await fetch('/api/rides/current/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            if (res.ok) {
                const ride = await res.json();
                rideId = ride.id;
            }
        } catch (e) { console.error("Fetch current failed", e); }

        if (!rideId) {
            alert("No active ride found to pay.");
            return;
        }

        setLoading('pay-now-btn', true);
        const payload = {
            ride_id: rideId,
            method: method
        };
        if (amount) payload.amount_paid = amount;

        try {
            const response = await fetch('/api/payments/initiate/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (response.ok) {
                if (method === 'CASH') {
                    alert(`Cash payment of ${amount} BDT recorded!`);
                    updateRideStatus('PAID', { id: rideId, amount_paid: amount });
                    fetchWalletStats();
                } else if (data.checkout_url) {
                    window.location.href = data.checkout_url;
                }
            } else {
                alert(data.error || "Payment initiation failed");
            }
        } catch (e) { alert("Action failed"); }
        setLoading('pay-now-btn', false);
    }

    window.handlePayment = async function () {
        showPaymentMethodModal();
    };

    window.payRide = async function (rideId, token) {
        setLoading('pay-now-btn', true);
        try {
            const response = await fetch('/api/payments/initiate/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify({ ride_id: rideId })
            });
            const data = await response.json();
            if (response.ok && data.GatewayPageURL) {
                window.location.href = data.GatewayPageURL;
            }
        } finally {
            setLoading('pay-now-btn', false);
        }
    };


    // ===== CHAT SYSTEM =====
    let currentChatRideId = null;
    let currentChatOtherId = null;
    let currentChatOtherName = null;

    window.openChat = function (rideId, otherId, otherName) {
        console.log('[Chat] Opening chat for ride:', rideId, 'with user:', otherId);
        currentChatRideId = rideId;
        currentChatOtherId = otherId;
        currentChatOtherName = otherName;

        const modal = document.getElementById('chat-modal');
        const title = document.getElementById('chat-title');
        if (modal) modal.style.display = 'flex';
        if (title) title.innerText = `Chat with ${otherName}`;

        loadChatMessages(rideId, otherId);
        startPolling();
    };

    window.closeChat = function () {
        const modal = document.getElementById('chat-modal');
        if (modal) modal.style.display = 'none';
        clearInterval(chatInterval);
        currentChatRideId = null;
        currentChatOtherId = null;
        currentChatOtherName = null;
    };

    async function loadChatMessages(rideId, otherUserId = null) {
        const token = localStorage.getItem('token');
        const messagesDiv = document.getElementById('chat-messages');
        if (!messagesDiv) return;

        // Use currentChatOtherId if not provided
        const targetOtherId = otherUserId || currentChatOtherId;

        try {
            let url = `/api/rides/messages/?ride_id=${rideId}`;
            if (targetOtherId) {
                url += `&other_user_id=${targetOtherId}`;
            }

            const res = await fetch(url, {
                headers: { 'Authorization': `Token ${token}` }
            });
            if (res.ok) {
                const messages = await res.json();
                displayChatMessages(messages);
            }
        } catch (e) {
            console.error('[Chat] Load error', e);
        }
    }

    function displayChatMessages(messages) {
        const messagesDiv = document.getElementById('chat-messages');
        if (!messagesDiv) return;

        const currentUserId = currentUser?.id;

        if (messages.length === 0) {
            messagesDiv.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">No messages yet.</p>';
            return;
        }

        messagesDiv.innerHTML = messages.map(msg => {
            const isOwn = msg.sender === currentUserId;
            const align = isOwn ? 'flex-end' : 'flex-start';
            const bg = isOwn ? '#3498db' : '#ecf0f1';
            const color = isOwn ? 'white' : '#2c3e50';

            return `
                <div style="display:flex;justify-content:${align};margin-bottom:8px;">
                    <div style="background:${bg};color:${color};padding:10px 14px;border-radius:12px;max-width:70%;word-wrap:break-word;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                        <p style="margin:0;font-size:14px;">${msg.content}</p>
                        <p style="margin:4px 0 0 0;font-size:10px;opacity:0.7;">${new Date(msg.timestamp).toLocaleTimeString()}</p>
                    </div>
                </div>
            `;
        }).join('');

        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    window.sendMessage = async function () {
        const input = document.getElementById('chat-input');
        const message = input?.value?.trim();
        if (!message || !currentChatRideId) {
            console.warn('[Chat] Cannot send: missing message or ride ID');
            return;
        }

        const token = localStorage.getItem('token');
        const originalMsg = input.value;
        input.value = '';

        try {
            // Using correct backend endpoint and field names
            const res = await fetch(`/api/rides/messages/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`
                },
                body: JSON.stringify({
                    ride: currentChatRideId,
                    receiver: currentChatOtherId,
                    content: message
                })
            });

            if (res.ok) {
                console.log('[Chat] Message sent successfully');
                loadChatMessages(currentChatRideId);
            } else {
                input.value = originalMsg;
                const errData = await res.json();
                alert(errData.error || 'Message send failed');
            }
        } catch (e) {
            console.error('[Chat] Send error', e);
            input.value = originalMsg;
            alert('Network error sending message');
        }
    };
    function stopJobPolling() {
        if (typeof chatInterval !== 'undefined') {
            clearInterval(chatInterval);
        }
    }

    function startPolling() {
        clearInterval(chatInterval);
        chatInterval = setInterval(() => {
            if (currentChatRideId) loadChatMessages(currentChatRideId, currentChatOtherId);
        }, 3000);
    }

    // Add Enter key listener for chat input
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    let notificationSocket = null;
    const notificationSound = new Audio('https://assets.mixkit.co/active_storage/sfx/2358/2358-preview.mp3'); // Professional notification sound

    function connectNotificationSocket() {
        const token = localStorage.getItem('token');
        if (!token || !currentUser || currentUser.profile.role !== 'DRIVER') {
            console.log("ConnectNotificationSocket skipped: Not a driver or no token.");
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/?token=${token}`;

        console.log("Connecting to Notification WebSocket:", wsUrl);
        notificationSocket = new WebSocket(wsUrl);

        notificationSocket.onopen = () => {
            console.log("Notification WebSocket connected successfully.");
        };

        notificationSocket.onmessage = (e) => {
            console.log("Notification received:", e.data);
            const data = JSON.parse(e.data);
            if (data.type === 'new_ride_request') {
                handleNewRideRequest(data.ride);
            }
        };

        notificationSocket.onclose = (e) => {
            console.log("Notification socket closed. Reconnecting in 5s...", e.reason);
            setTimeout(connectNotificationSocket, 5000);
        };

        notificationSocket.onerror = (err) => {
            console.error("Notification WebSocket error:", err);
        };
    }
    window.connectNotificationSocket = connectNotificationSocket;

    function handleNewRideRequest(ride, allowRefresh = true) {
        // If we are here, we should show it. Polling only runs if online anyway.
        if (currentUser && currentUser.profile) {
            notificationSound.play().catch(e => console.log("Sound play failed", e));

            const jobText = document.getElementById('job-status-text');
            const acceptBtn = document.getElementById('job-accept-btn');

            if (jobText && acceptBtn) {
                jobText.innerHTML = `
                    <div style="background: #fff8e1; padding: 12px; border-radius: 12px; border: 1px solid #ffe082; margin-bottom: 15px;">
                        <p style="font-weight: 800; color: #f57f17; margin-bottom: 8px;"><i class="fas fa-bell"></i> NEW RIDE REQUEST!</p>
                        <p style="font-size: 14px; margin-bottom: 4px;"><strong>From:</strong> ${formatAddressDisplay(ride.pickup_address)}</p>
                        <p style="font-size: 14px; margin-bottom: 8px;"><strong>To:</strong> ${formatAddressDisplay(ride.drop_address)}</p>
                        <p style="font-size: 16px; font-weight: 700; color: #2ecc71;">Fare: ${ride.estimated_fare} BDT</p>
                    </div>
                `;
                acceptBtn.style.display = 'block';
                acceptBtn.innerText = "ACCEPT RIDE NOW";
                acceptBtn.onclick = () => acceptRide(ride.id);
            }

            // Optional: Show a nice browser notification if permission granted
            if (Notification.permission === "granted") {
                new Notification("New Ride Request!", {
                    body: `From: ${formatAddressDisplay(ride.pickup_address)}`,
                    icon: '/static/img/favicon.png'
                });
            }

            // Auto-refresh the available requests list if the modal is open
            if (allowRefresh) {
                const availableRequestsModal = document.getElementById('available-requests-modal');
                if (availableRequestsModal && availableRequestsModal.style.display === 'flex') {
                    showAvailableRequests();
                }
            }

            updateAvailableCount();
        }
    }

    window.acceptRide = async function (rideId, btnId = 'job-accept-btn') {
        const token = localStorage.getItem('token');
        setLoading(btnId, true);
        try {
            const response = await fetch(`/api/rides/${rideId}/action/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify({ action: 'ACCEPT' })
            });
            const data = await response.json();
            if (response.ok) {
                alert("Ride Accepted!");
                connectWebSocket(rideId, token, true);

                // Clear the available notification
                const jobText = document.getElementById('job-status-text');
                if (jobText) jobText.innerHTML = '<i class="fas fa-car"></i> You are on a ride!';

                updateAvailableCount();

                const finishBtn = document.getElementById('job-finish-btn');
                const chatBtn = document.getElementById('job-chat-btn');

                const controls = document.getElementById('job-active-controls');
                if (controls) controls.style.display = 'flex';

                if (finishBtn) finishBtn.onclick = () => finishRide(rideId);

                if (chatBtn && data.ride) {
                    const riderId = data.ride.rider;
                    const riderName = data.ride.rider_username || 'Rider';
                    chatBtn.onclick = () => openChat(rideId, riderId, riderName);
                }
            } else {
                alert(data.error || "Could not accept ride");
            }
        } finally {
            setLoading(btnId, false);
        }
    };

    window.finishRide = async function (rideId) {
        const token = localStorage.getItem('token');
        try {
            const response = await fetch(`/api/rides/${rideId}/status/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify({ status: 'COMPLETED' })
            });
            if (response.ok) {
                alert("Trip Finished! Please wait for payment.");
                // Note: WebSocket status_update will handle the UI refreshment
            }
        } catch (e) { alert("Action failed"); }
    };

    window.confirmFinishRide = async function (rideId) {
        if (!rideId) {
            console.error("confirmFinishRide called with invalid ID:", rideId);
            alert("Error: Invalid Ride ID");
            return;
        }
        const token = localStorage.getItem('token');
        try {
            const response = await fetch(`/api/rides/${rideId}/status/`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Token ${token}` },
                body: JSON.stringify({ status: 'FINISHED' })
            });
            if (response.ok) {
                alert("Ride officially closed!");
                fetchWalletStats(); // Refresh stats after ride finish
                // Note: WebSocket status_update will trigger 'FINISHED' in updateRideStatus 
                // which handles final cleanup and resetSelection.
            }
        } catch (e) { alert("Action failed"); }
    };




    // --- History & Stats ---
    window.showRideHistory = async function () {
        const token = localStorage.getItem('token');
        if (!token) return;

        const modal = document.getElementById('history-modal');
        const list = document.getElementById('history-list');
        modal.style.display = 'flex';
        list.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">Fetching history...</p>';

        try {
            const res = await fetch('/api/rides/history/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            const rides = await res.json();
            if (rides.length === 0) {
                list.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">No rides found.</p>';
                return;
            }

            list.innerHTML = rides.map(r => `
            <div style="background: white; padding: 18px; border-radius: 16px; margin-bottom: 12px; border: 1px solid #eee; box-shadow: 0 4px 10px rgba(0,0,0,0.02);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <span style="font-weight: 800; color: #333; font-size: 14px;">Ride #${r.id}</span>
                        <span style="display: block; font-size: 10px; color: #aaa;">${formatRideDate(r.created_at)}</span>
                    </div>
                    <span style="background: ${r.status === 'PAID' ? '#eef7f2' : '#f1f5f9'}; color: ${r.status === 'PAID' ? '#27ae60' : '#475569'}; padding: 4px 10px; border-radius: 20px; font-size: 10px; font-weight: 800; text-transform: uppercase;">${r.status}</span>
                </div>
                <div style="background: #f8f9fa; padding: 12px; border-radius: 12px; margin-bottom: 12px;">
                    <p style="font-size: 13px; color: #444; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-circle-dot" style="color: #2ecc71; width: 14px; font-size: 10px;"></i>
                        <span style="flex: 1;">${formatAddressDisplay(r.pickup_address)}</span>
                    </p>
                    <p style="font-size: 13px; color: #444; margin: 0; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-location-pin" style="color: #e74c3c; width: 14px; font-size: 12px;"></i>
                        <span style="flex: 1;">${formatAddressDisplay(r.drop_address)}</span>
                    </p>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 800; color: #27ae60; font-size: 16px;">${r.estimated_fare} BDT</span>
                    <div style="font-size: 11px; color: #94a3b8; font-weight: 600;">
                        ${r.driver_username ? `<i class="fas fa-user-circle"></i> ${r.driver_username}` : ''}
                    </div>
                </div>
            </div>
        `).join('');
        } catch (e) { list.innerHTML = 'Error loading history'; }
    };

    window.hideHistoryModal = () => document.getElementById('history-modal').style.display = 'none';

    window.showInbox = async function () {
        const token = localStorage.getItem('token');
        if (!token) return;

        const modal = document.getElementById('inbox-modal');
        const list = document.getElementById('inbox-list');
        modal.style.display = 'flex';
        list.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">Loading conversations...</p>';

        try {
            const res = await fetch('/api/rides/chats/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            const chats = await res.json();

            if (chats.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px;">
                        <i class="fas fa-comments" style="font-size: 48px; color: #eee; margin-bottom: 16px;"></i>
                        <p style="color: #888;">No messages yet.</p>
                    </div>`;
                return;
            }

            list.innerHTML = chats.map(c => `
                <div onclick="openChat(${c.ride_id}, ${c.other_user_id}, '${c.other_username}'); hideInboxModal();" 
                     style="padding: 16px; border-bottom: 1px solid #eee; cursor: pointer; display: flex; align-items: center; gap: 12px; transition: background 0.2s;">
                    <div style="width: 44px; height: 44px; background: #3498db; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;">
                        ${c.other_username.charAt(0).toUpperCase()}
                    </div>
                    <div style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: 700; color: #333;">${c.other_username}</span>
                            <span style="font-size: 10px; color: #999;">${new Date(c.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <p style="font-size: 13px; color: #666; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${c.last_message}
                        </p>
                    </div>
                </div>
            `).join('');
        } catch (e) { list.innerHTML = 'Error loading messages'; }
    };

    window.hideInboxModal = () => document.getElementById('inbox-modal').style.display = 'none';

    window.showAvailableRequests = async function (providedRides = null) {
        localStorage.setItem('currentView', 'AVAILABLE_REQUESTS');
        const token = localStorage.getItem('token');
        if (!token) return;

        const modal = document.getElementById('available-requests-modal');
        const list = document.getElementById('available-requests-list');
        // Only show modal if not provided data source (explicit user click) 
        // OR if it's already open (polling update)
        if (!providedRides) modal.style.display = 'flex';

        if (!providedRides) {
            list.innerHTML = '<p style="text-align: center; color: #888; padding: 20px;">Fetching requests...</p>';
        }

        try {
            let rides = providedRides;
            if (!rides) {
                const res = await fetch('/api/rides/available/', {
                    headers: { 'Authorization': `Token ${token}` }
                });
                rides = await res.json();
            }

            if (rides.length === 0) {
                list.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px;">
                        <i class="fas fa-clipboard-list" style="font-size: 48px; color: #eee; margin-bottom: 16px;"></i>
                        <p style="color: #888;">No pending ride requests at the moment.</p>
                    </div>`;
                return;
            }

            list.innerHTML = rides.map(r => `
                <div style="background: #fff; padding: 18px; border-radius: 16px; border: 1px solid #eee; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                        <div>
                            <p style="font-size: 11px; font-weight: 800; color: #999; margin-bottom: 2px; text-transform: uppercase;">Request #${r.id}</p>
                            <p style="font-size: 14px; font-weight: 700; color: #333; margin: 0;">${r.rider_username}</p>
                        </div>
                        <div style="text-align: right;">
                            <span style="display: block; color: #27ae60; font-size: 16px; font-weight: 800;">${r.estimated_fare} BDT</span>
                            <span style="font-size: 10px; color: #aaa;">${formatRideDate(r.created_at)}</span>
                        </div>
                    </div>
                    <div style="background: #f8f9fa; padding: 12px; border-radius: 12px; font-size: 13px; color: #444; margin-bottom: 16px;">
                        <p style="margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-circle-dot" style="color: #2ecc71; width: 14px; font-size: 10px;"></i> 
                            <span style="flex: 1;">${formatAddressDisplay(r.pickup_address)}</span>
                        </p>
                        <p style="display: flex; align-items: center; gap: 8px; margin: 0;">
                            <i class="fas fa-location-pin" style="color: #e74c3c; width: 14px; font-size: 12px;"></i> 
                            <span style="flex: 1;">${formatAddressDisplay(r.drop_address)}</span>
                        </p>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn btn-secondary btn-sm" onclick="previewRideOnMap(${JSON.stringify(r).replace(/"/g, '&quot;')})" style="flex: 1; border-radius: 12px; background: #f0f4f8; color: #3498db; font-weight: 700; border: none;">
                             <i class="fas fa-map"></i> View Map
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="acceptRide(${r.id}); hideAvailableRequestsModal();" style="flex: 1; border-radius: 12px; background: #2ecc71; font-weight: 800; border: none; box-shadow: 0 4px 10px rgba(46, 204, 113, 0.2);">
                            Accept
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error("Available requests load fail", e);
            list.innerHTML = '<p style="color: red; text-align: center; padding: 20px;">Failed to load available requests. Please try again.</p>';
        }
    };

    window.updateAvailableCount = async function () {
        const token = localStorage.getItem('token');
        const countEl = document.getElementById('available-count');
        if (!token || !countEl) return;

        try {
            const res = await fetch('/api/rides/available/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            if (res.ok) {
                const rides = await res.json();
                countEl.innerText = rides.length;
                countEl.style.display = rides.length > 0 ? 'inline-block' : 'none';
            }
        } catch (e) {
            console.error("Update available count failed", e);
        }
    };

    window.hideAvailableRequestsModal = () => {
        localStorage.removeItem('currentView');
        document.getElementById('available-requests-modal').style.display = 'none';
    };

    // Request Notification permission on first interaction
    document.addEventListener('click', () => {
        if (Notification.permission === "default") {
            Notification.requestPermission();
        }
    }, { once: true });

    // --- My Requests Logic ---
    let editingRideId = null;

    window.showMyRequests = async function () {
        const modal = document.getElementById('my-requests-modal');
        const list = document.getElementById('my-requests-list');
        const token = localStorage.getItem('token');

        if (!token) {
            Auth.showModal('login');
            return;
        }

        modal.style.display = 'flex';
        list.innerHTML = '<p style="text-align: center; padding: 20px;">Loading requests...</p>';

        try {
            const response = await fetch('/api/rides/my-requests/', {
                headers: { 'Authorization': `Token ${token}` }
            });
            const rides = await response.json();

            if (rides.length === 0) {
                list.innerHTML = '<p style="text-align: center; padding: 20px; color: #888;">No active requests.</p>';
                return;
            }

            list.innerHTML = rides.map(ride => {
                const canEdit = ride.status === 'REQUESTED';
                const canCancel = ['REQUESTED', 'ASSIGNED'].includes(ride.status);
                let badgeColor = '#3498db';
                if (ride.status === 'COMPLETED') badgeColor = '#27ae60';
                if (ride.status === 'CANCELLED') badgeColor = '#e74c3c';

                return `
                    <div style="background: white; padding: 18px; border-radius: 16px; margin-bottom: 12px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <div>
                                <span style="font-weight: 800; color: #333; font-size: 14px;">Ride #${ride.id}</span>
                                <span style="display: block; font-size: 10px; color: #aaa;">${formatRideDate(ride.created_at)}</span>
                            </div>
                            <span style="font-size: 10px; padding: 4px 10px; background: ${badgeColor}; color: white; border-radius: 20px; font-weight: 800; text-transform: uppercase;">${ride.status}</span>
                        </div>
                        <div style="background: #f8f9fa; padding: 12px; border-radius: 12px; margin-bottom: 12px;">
                            <p style="font-size: 13px; color: #444; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-circle-dot" style="color: #2ecc71; width: 14px; font-size: 10px;"></i>
                                <span style="flex: 1;">${formatAddressDisplay(ride.pickup_address)}</span>
                            </p>
                            <p style="font-size: 13px; color: #444; margin: 0; display: flex; align-items: center; gap: 8px;">
                                <i class="fas fa-location-pin" style="color: #e74c3c; width: 14px; font-size: 12px;"></i>
                                <span style="flex: 1;">${formatAddressDisplay(ride.drop_address)}</span>
                            </p>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <span style="font-weight: 800; color: #27ae60; font-size: 18px;">${ride.estimated_fare} BDT</span>
                        </div>
                        
                        <div style="display: flex; gap: 10px;">
                            <button class="btn btn-secondary btn-sm" onclick="previewRideOnMap(${JSON.stringify(ride).replace(/"/g, '&quot;')}, true)" 
                                style="flex: 1; padding: 10px; background: #f0f4f8; color: #3498db; font-weight: 700; border-radius: 12px; border: none;">
                                <i class="fas fa-map"></i> View Map
                            </button>
                            ${canEdit ? `
                                <button class="btn btn-primary btn-sm" onclick="editRide(${ride.id})" 
                                    style="flex: 1; padding: 10px; background: #f39c12; color: white; border-radius: 12px; font-weight: 700; border: none;">Edit</button>` : ''}
                            ${canCancel ? `
                                <button class="btn btn-secondary btn-sm" onclick="cancelRide(${ride.id})"
                                    style="width: 44px; padding: 0; background: #fee2e2; color: #ef4444; border-radius: 12px; border: none; display: flex; align-items: center; justify-content: center;">
                                    <i class="fas fa-trash"></i>
                                </button>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) {
            console.error(e);
            list.innerHTML = '<p style="color: red; text-align: center;">Failed to load requests.</p>';
        }
    };

    window.hideMyRequestsModal = () => document.getElementById('my-requests-modal').style.display = 'none';

    window.cancelRide = async function (rideId) {
        if (!confirm("Are you sure you want to DELETE this ride request directly from the database?")) return;

        const token = localStorage.getItem('token');
        try {
            const response = await fetch(`/api/rides/${rideId}/cancel/`, {
                method: 'POST',
                headers: { 'Authorization': `Token ${token}` }
            });
            const data = await response.json();
            if (response.ok) {
                alert("Ride deleted.");
                showMyRequests(); // Refresh
                if (currentUser.profile.role === 'RIDER') initDashboard(); // Refresh dashboard state if needed
            } else {
                alert("Failed: " + data.error);
            }
        } catch (e) { console.error(e); }
    };

    // ... (editRide remains same until update needed)

    // --- Generic Map Preview ---
    window.previewRideOnMap = function (ride, isPassenger = false) {
        // Hide Selector & Modals
        const selector = document.getElementById('rajbari-location-selector');
        if (selector) selector.style.display = 'none';

        if (isPassenger) hideMyRequestsModal();
        else hideAvailableRequestsModal();

        // Setup Map
        if (pickupMarker) map.removeLayer(pickupMarker);
        if (dropMarker) map.removeLayer(dropMarker);

        const pickup = { lat: parseFloat(ride.pickup_lat), lng: parseFloat(ride.pickup_lng) };
        const drop = { lat: parseFloat(ride.drop_lat), lng: parseFloat(ride.drop_lng) };

        pickupMarker = L.marker(pickup, {
            icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-circle-dot" style="color:black"></i>', iconAnchor: [12, 12] })
        }).addTo(map);

        dropMarker = L.marker(drop, {
            icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-location-pin" style="color:black"></i>', iconAnchor: [12, 12] })
        }).addTo(map);

        drawRoute(pickup, drop);

        // Show Overlay
        const overlay = document.getElementById('map-preview-controls');
        overlay.style.display = 'flex';
        document.getElementById('preview-fare').innerText = ride.estimated_fare + " BDT";
        document.getElementById('preview-route-info').innerHTML = `
        <strong>From:</strong> ${ride.pickup_address || 'Nearby'} <br>
        <strong>To:</strong> ${ride.drop_address || 'Destination'}
    `;

        const acceptBtn = document.getElementById('preview-accept-btn');
        const backBtn = document.getElementById('preview-back-btn');

        // Toggle Buttons based on role
        if (isPassenger) {
            if (acceptBtn) acceptBtn.style.display = 'none';
            backBtn.onclick = () => closePreviewMode(true);
        } else {
            if (acceptBtn) {
                acceptBtn.style.display = 'block';
                acceptBtn.onclick = () => {
                    acceptRide(ride.id, 'preview-accept-btn');
                    closePreviewMode(false);
                };
            }
            backBtn.onclick = () => closePreviewMode(false);
        }
    };

    window.closePreviewMode = function (isPassenger = false) {
        document.getElementById('map-preview-controls').style.display = 'none';

        const selector = document.getElementById('rajbari-location-selector');
        if (selector) selector.style.display = 'block';

        resetSelection();

        // Re-open previous modal
        if (isPassenger) showMyRequests();
        else showAvailableRequests();
    };

    window.editRide = async function (rideId) {
        const token = localStorage.getItem('token');
        try {
            // Fetch fresh details or pass them? Fetching is safer.
            const response = await fetch(`/api/rides/${rideId}/`, {
                headers: { 'Authorization': `Token ${token}` }
            });
            const ride = await response.json();

            // Populate map
            hideMyRequestsModal();
            resetSelection();

            // Set locations
            pickupLatLng = { lat: parseFloat(ride.pickup_lat), lng: parseFloat(ride.pickup_lng) };
            dropLatLng = { lat: parseFloat(ride.drop_lat), lng: parseFloat(ride.drop_lng) };

            pickupMarker = L.marker(pickupLatLng, {
                icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-circle-dot" style="color:black"></i>', iconAnchor: [12, 12] })
            }).addTo(map);

            dropMarker = L.marker(dropLatLng, {
                icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-location-pin" style="color:black"></i>', iconAnchor: [12, 12] })
            }).addTo(map);

            // Draw Route (Road)
            drawRoute(pickupLatLng, dropLatLng);

            // Set Edit Mode
            editingRideId = rideId;
            const reqBtn = document.getElementById('request-ride-btn');
            reqBtn.innerText = "Update Request";
            reqBtn.style.background = "#e67e22"; // Orange for update

            // Add a cancel edit button
            let cancelEditBtn = document.getElementById('cancel-edit-btn');
            if (!cancelEditBtn) {
                cancelEditBtn = document.createElement('button');
                cancelEditBtn.id = 'cancel-edit-btn';
                cancelEditBtn.className = 'btn btn-secondary';
                cancelEditBtn.innerText = 'Cancel Edit';
                cancelEditBtn.style.marginTop = '10px';
                cancelEditBtn.onclick = () => {
                    resetSelection();
                    reqBtn.innerText = "Request Ride";
                    reqBtn.style.background = ""; // Reset
                    editingRideId = null;
                    cancelEditBtn.remove();
                };
                reqBtn.parentNode.insertBefore(cancelEditBtn, reqBtn.nextSibling);
            }

            alert("Adjust locations on map if needed, then click Update Request.");

        } catch (e) { console.error(e); alert("Could not load ride for editing"); }
    };
    // Removed closing brace to extend scope for Rajbari logic

    // --- Rajbari Location Logic ---
    // --- Rajbari Location Logic ---
    window.toggleLocationPanel = function () {
        const el = document.getElementById('loc-panel-content');
        const icon = document.getElementById('loc-panel-icon');
        if (el.style.display === 'none') {
            el.style.display = 'flex';
            icon.className = 'fas fa-chevron-up';
            populateRouteUpazilas();
        } else {
            el.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    };

    function populateRouteUpazilas() {
        console.log("Populating Upazilas...");
        if (typeof RAJBARI_LOCATIONS === 'undefined') {
            console.error("RAJBARI_LOCATIONS is undefined!");
            return;
        }

        // Populate BOTH pickup and drop upazila dropdowns
        ['pickup', 'drop'].forEach(type => {
            const sel = document.getElementById(`${type}-upazila`);
            if (!sel) return;

            // If already populated, skip
            if (sel.options.length > 1) return;

            const locations = window.RAJBARI_LOCATIONS;
            if (!locations) {
                console.error("Rajbari Locations data missing on window object");
                return;
            }

            for (let u in locations) {
                let opt = document.createElement('option');
                opt.value = u;
                opt.innerText = u;
                sel.appendChild(opt);
            }
        });
    }

    window.loadUnionList = function (type) {
        const upazila = document.getElementById(`${type}-upazila`).value;
        const unionSel = document.getElementById(`${type}-union`);
        const villageIn = document.getElementById(`${type}-village`);

        unionSel.innerHTML = '<option value="">Select Union</option>';
        unionSel.disabled = true;
        villageIn.disabled = true;

        if (!upazila) return;

        // Optional: Center map on Upazila only if it's the first interaction? 
        // Maybe better to wait for specific selection to avoid jumping around.

        const centers = window.UPAZILA_CENTERS;
        if (centers && centers[upazila]) {
            const latLng = centers[upazila];
            map.setView(latLng, 13);

            // Immediate coarse marker placement at Upazila level
            if (type === 'pickup') {
                if (pickupMarker) map.removeLayer(pickupMarker);
                pickupMarker = L.marker(latLng, {
                    icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-circle-dot" style="color:green; font-size: 24px;"></i>', iconAnchor: [12, 12] })
                }).addTo(map);
                pickupLatLng = latLng;
                pickupAddress = upazila + ", Rajbari";
            } else {
                if (dropMarker) map.removeLayer(dropMarker);
                dropMarker = L.marker(latLng, {
                    icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-map-marker-alt" style="color:red; font-size: 24px;"></i>', iconAnchor: [12, 24] })
                }).addTo(map);
                dropLatLng = latLng;
                dropAddress = upazila + ", Rajbari";
            }
            updateAddressUI();
            if (pickupLatLng && dropLatLng) getFareEstimate();
        }

        const locations = window.RAJBARI_LOCATIONS;
        if (!locations || !locations[upazila]) return;

        const unions = locations[upazila];
        for (let u in unions) {
            let opt = document.createElement('option');
            opt.value = u;
            opt.innerText = u;
            unionSel.appendChild(opt);
        }
        unionSel.disabled = false;
    };

    window.updateLocation = function (type) {
        const upazila = document.getElementById(`${type}-upazila`).value;
        const union = document.getElementById(`${type}-union`).value;
        const villageIn = document.getElementById(`${type}-village`);
        const village = villageIn.value;

        if (!upazila) return;
        villageIn.disabled = !union;

        // Build a prioritized list of queries to try
        let queries = [];

        if (village && union) {
            queries.push(`${village}, ${union}, ${upazila}, Rajbari, Bangladesh`);
            queries.push(`${village}, ${upazila}, Rajbari, Bangladesh`);
            queries.push(`${union}, ${upazila}, Rajbari, Bangladesh`);
        } else if (union) {
            queries.push(`${union} Union Parishad, ${upazila}, Rajbari, Bangladesh`);
            queries.push(`${union} Union, ${upazila}, Rajbari, Bangladesh`);
            queries.push(`${union}, ${upazila}, Rajbari, Bangladesh`);
            queries.push(`${union}, Rajbari, Bangladesh`);
        } else {
            queries.push(`${upazila} Upazila, Rajbari, Bangladesh`);
            queries.push(`${upazila}, Rajbari, Bangladesh`);
        }

        // Final ultimate fallback
        queries.push("Rajbari, Bangladesh");

        const friendlyName = [village, union, upazila, "Rajbari"].filter(x => x).join(", ");
        searchLocationForRoute(queries, type, friendlyName);
    };

    async function searchLocationForRoute(queries, type, friendlyName = null) {
        console.log(`Searching for ${type}... Trying multiple queries.`);

        for (let query of queries) {
            try {
                const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
                const data = await response.json();

                if (data && data.length > 0) {
                    const lat = parseFloat(data[0].lat);
                    const lng = parseFloat(data[0].lon);
                    const latLng = { lat, lng };

                    console.log(`Found ${type} at: ${query}`, latLng);

                    // Store the friendly name if provided, else use query
                    if (type === 'pickup') pickupAddress = friendlyName || query;
                    else dropAddress = friendlyName || query;

                    updateAddressUI();

                    // Update Map Markers
                    if (type === 'pickup') {
                        if (pickupMarker) map.removeLayer(pickupMarker);
                        pickupMarker = L.marker(latLng, {
                            icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-circle-dot" style="color:green; font-size: 24px;"></i>', iconAnchor: [12, 12] })
                        }).addTo(map);
                        pickupLatLng = latLng;
                    } else {
                        if (dropMarker) map.removeLayer(dropMarker);
                        dropMarker = L.marker(latLng, {
                            icon: L.divIcon({ className: 'custom-icon', html: '<i class="fas fa-map-marker-alt" style="color:red; font-size: 24px;"></i>', iconAnchor: [12, 24] })
                        }).addTo(map);
                        dropLatLng = latLng;
                    }

                    map.setView(latLng, 14);

                    if (pickupLatLng && dropLatLng) {
                        getFareEstimate();
                    }
                    return; // Stop searching once found
                }
            } catch (e) {
                console.warn(`Search attempt failed for: ${query}`, e);
            }
        }
        console.error("No location found for any query combination.");
    }

    // --- Draggable Bottom Sheet Logic ---
    const sheet = document.getElementById('bottom-sheet');
    const dragHandle = sheet.querySelector('.drag-handle');
    let isDragging = false;
    let startY, startHeight;

    const SNAP_POINTS = {
        COLLAPSED: window.innerHeight * 0.9,
        HALF: window.innerHeight * 0.5,
        FULL: window.innerHeight * 0.1
    };

    function updateSheetHeight(height) {
        const MIN_TOP = SNAP_POINTS.FULL;
        const MAX_TOP = SNAP_POINTS.COLLAPSED;
        const clampedHeight = Math.max(MIN_TOP, Math.min(height, MAX_TOP));
        sheet.style.top = clampedHeight + 'px';
        sheet.style.height = (window.innerHeight - clampedHeight) + 'px';

        // Reposition Map Controls above the sheet
        const mapControls = document.getElementById('map-controls');
        if (mapControls) {
            const visibleSheetTop = clampedHeight;
            const distanceForControls = window.innerHeight - visibleSheetTop;
            mapControls.style.bottom = (distanceForControls + 20) + 'px';
        }
    }

    function snapToPoint(currentY) {
        sheet.classList.add('snapping');

        const distToCollapsed = Math.abs(currentY - SNAP_POINTS.COLLAPSED);
        const distToHalf = Math.abs(currentY - SNAP_POINTS.HALF);
        const distToFull = Math.abs(currentY - SNAP_POINTS.FULL);

        const minDist = Math.min(distToCollapsed, distToHalf, distToFull);

        if (minDist === distToCollapsed) updateSheetHeight(SNAP_POINTS.COLLAPSED);
        else if (minDist === distToHalf) updateSheetHeight(SNAP_POINTS.HALF);
        else updateSheetHeight(SNAP_POINTS.FULL);

        setTimeout(() => sheet.classList.remove('snapping'), 300);
    }

    const onDragStart = (e) => {
        isDragging = true;
        startY = (e.type === 'touchstart') ? e.touches[0].clientY : e.clientY;
        startHeight = sheet.offsetTop;
        sheet.style.transition = 'none';
        document.body.style.overflow = 'hidden';
    };

    const onDrag = (e) => {
        if (!isDragging) return;
        const currentY = (e.type === 'touchmove') ? e.touches[0].clientY : e.clientY;
        const delta = currentY - startY;
        updateSheetHeight(startHeight + delta);
    };

    const onDragEnd = (e) => {
        if (!isDragging) return;
        isDragging = false;
        const currentY = sheet.offsetTop;
        snapToPoint(currentY);
        document.body.style.overflow = '';
    };

    dragHandle.addEventListener('mousedown', onDragStart);
    dragHandle.addEventListener('touchstart', onDragStart, { passive: true });

    window.addEventListener('mousemove', onDrag);
    window.addEventListener('touchmove', onDrag, { passive: false });

    window.addEventListener('mouseup', onDragEnd);
    window.addEventListener('touchend', onDragEnd);

    // Initial State: Half
    updateSheetHeight(SNAP_POINTS.HALF);

    // Initialize on load to ensure data is ready
    window.addEventListener('load', function () {
        console.log("Window loaded, initializing Rajbari locations...");
        setTimeout(populateRouteUpazilas, 500); // Small delay to ensure everything is parsed
    });

});
