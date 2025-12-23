"""
Production Fixes Auto-Patcher
Automatically injects critical fixes into main.js
"""

import re

def patch_main_js(file_path):
    print(f"📝 Patching {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Add State Persistence Helper (after line ~19)
    state_helper = '''
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
'''
    
    # Insert after bangladeshBounds definition
    if 'const bangladeshBounds' in content and '// ===== STATE PERSISTENCE HELPER =====' not in content:
        content = content.replace(
            '};',  # After bangladeshBounds
            f'}};{state_helper}',
            1  # Only first occurrence
        )
        print("✅ Added State Persistence Helper")
    
    # Fix 2: Add Chat Functions (before sendMessage)
    chat_functions = '''
    // ===== CHAT SYSTEM =====
    let currentChatRideId = null;
    let currentChatOtherId = null;
    let currentChatOtherName = null;

    window.openChat = function(rideId, otherId, otherName) {
        console.log('[Chat] Opening chat for ride:', rideId);
        currentChatRideId = rideId;
        currentChatOtherId = otherId;
        currentChatOtherName = otherName;
        
        const modal = document.getElementById('chat-modal');
        const title = document.getElementById('chat-title');
        if (modal) modal.style.display = 'flex';
        if (title) title.innerText = `Chat with ${otherName}`;
        
        loadChatMessages(rideId);
    };

    window.closeChat = function() {
        const modal = document.getElementById('chat-modal');
        if (modal) modal.style.display = 'none';
        currentChatRideId = null;
        currentChatOtherId = null;
        currentChatOtherName = null;
    };

    async function loadChatMessages(rideId) {
        const token = localStorage.getItem('token');
        const messagesDiv = document.getElementById('chat-messages');
        if (!messagesDiv) return;
        
        messagesDiv.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">Loading messages...</p>';
        
        try {
            const res = await fetch(`/api/chat/messages/${rideId}/`, {
                headers: { 'Authorization': `Token ${token}` }
            });
            if (res.ok) {
                const messages = await res.json();
                displayChatMessages(messages);
            } else {
                messagesDiv.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">No messages yet. Start chatting!</p>';
            }
        } catch (e) {
            console.error('[Chat] Load error', e);
            messagesDiv.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">Could not load messages.</p>';
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
                        <p style="margin:0;font-size:14px;">${msg.message}</p>
                        <p style="margin:4px 0 0 0;font-size:10px;opacity:0.7;">${new Date(msg.timestamp).toLocaleTimeString()}</p>
                    </div>
                </div>
            `;
        }).join('');
        
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
    // ===== END CHAT SYSTEM =====
'''
    
    # Insert before sendMessage function
    if 'window.sendMessage = async function' in content and '// ===== CHAT SYSTEM =====' not in content:
        content = content.replace(
            'window.sendMessage = async function',
            f'{chat_functions}\n    window.sendMessage = async function'
        )
        print("✅ Added Chat System Functions")
    
    # Fix 3: Update sendMessage function
    old_send_message = r'window\.sendMessage = async function \(\) \{[^}]+\}'
    new_send_message = '''window.sendMessage = async function() {
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
            const res = await fetch(`/api/chat/send/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${token}`
                },
                body: JSON.stringify({
                    ride_id: currentChatRideId,
                    message: message
                })
            });
            
            if (res.ok) {
                console.log('[Chat] Message sent successfully');
                loadChatMessages(currentChatRideId);
            } else {
                input.value = originalMsg;
                alert('Message send failed');
            }
        } catch (e) {
            console.error('[Chat] Send error', e);
            input.value = originalMsg;
            alert('Network error sending message');
        }
    }'''
    
    # Only replace if not already updated
    if 'loadChatMessages(currentChatRideId)' not in content:
        content = re.sub(old_send_message, new_send_message, content, flags=re.DOTALL)
        print("✅ Updated sendMessage Function")
    
    # Fix 4: Enhance checkActiveRide
    old_check_active = r'async function checkActiveRide\(\) \{[^}]+\}'
    new_check_active = '''async function checkActiveRide() {
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
    }'''
    
    # Only replace if not already enhanced
    if 'RideState.load()' not in content:
        content = re.sub(old_check_active, new_check_active, content, flags=re.DOTALL)
        print("✅ Enhanced checkActiveRide Function")
    
    # Fix 5: Add state saving in updateRideStatus (at the end of function)
    # Find the last line before closing brace of updateRideStatus
    state_save_code = '''
        // Save state for persistence across reloads
        if (details && details.id) {
            const stateData = {...details, status: status};
            RideState.save(stateData);
        }'''
    
    if 'function updateRideStatus(' in content and 'RideState.save(stateData)' not in content:
        # Find the end of updateRideStatus function (look for specific pattern)
        pattern = r'(function updateRideStatus\(status, details = \{\}\) \{.*?)(    \}\r?\n)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            content = content[:match.end(1)] + state_save_code + '\n' + content[match.end(1):]
            print("✅ Added State Saving in updateRideStatus")
    
    # Write patched content
    backup_path = file_path.replace('.js', '.backup.js')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"💾 Backup saved: {backup_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Successfully patched {file_path}!")
    print("\n🎯 Applied Fixes:")
    print("  1. ✅ State Persistence Helper")
    print("  2. ✅ Chat System (openChat, loadChatMessages, displayChatMessages)")
    print("  3. ✅ Enhanced sendMessage")
    print("  4. ✅ Improved checkActiveRide with cache")
    print("  5. ✅ State saving in updateRideStatus")
    print("\n📝 Next Steps:")
    print("  1. Test locally: python manage.py runserver")
    print("  2. Test features: refresh, chat, ride flow")
    print("  3. Push to GitHub and deploy to Railway")

if __name__ == '__main__':
    import sys
    file_path = r'C:\Users\nafiz\Desktop\Project Ultra\Rajbari Ride\backend\static\js\main.js'
    
    try:
        patch_main_js(file_path)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
