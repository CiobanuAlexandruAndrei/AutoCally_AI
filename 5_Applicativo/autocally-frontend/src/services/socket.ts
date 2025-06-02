import { io } from 'socket.io-client'

// Use same backend URL configuration as api.ts
//const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://localhost:5001'
const backendUrl = 'https://172.20.0.14:6969'
const SOCKET_URL = backendUrl.startsWith('https://') ? backendUrl : `https://${backendUrl}`

// Silenced console log for debugging
// console.log('WebSocket connecting to:', SOCKET_URL)

export const socket = io(SOCKET_URL, {
  autoConnect: false,
  transports: ['websocket'],
  path: '/socket.io',
  secure: true,
  rejectUnauthorized: false,  // Accept self-signed certificates in both dev and prod for Docker
  reconnection: true,         // Enable reconnection
  reconnectionAttempts: 5,    // Try to reconnect 5 times
  reconnectionDelay: 1000,    // Wait 1 second between attempts
  timeout: 20000             // Connection timeout after 20 seconds
})

// Silenced SSL error handler
socket.on('connect_error', (error) => {
  // console.error('Socket connection error:', error.message)
  if (error.message.includes('SSL')) {
    // console.warn('SSL certificate issue, but continuing with connection attempt...')
  }
})

// Silenced general error handler
socket.on('error', (error) => {
  // console.error('Socket error:', error)
})

// Silenced reconnect handlers
socket.on('reconnect', (attemptNumber) => {
  // console.log('Socket reconnected after', attemptNumber, 'attempts')
})

socket.on('reconnect_attempt', (attemptNumber) => {
  // console.log('Socket attempting to reconnect:', attemptNumber)
})

socket.on('reconnect_error', (error) => {
  // console.error('Socket reconnection error:', error)
})

socket.on('reconnect_failed', () => {
  // console.error('Socket reconnection failed after all attempts')
})

// Silenced connection and disconnection events
socket.on('connect', () => {
  // console.log('Socket connected successfully')
  
  // Listen for connection established event
  socket.on('connection_established', (data) => {
    // console.log('Connection established with server:', data)
  })
})

socket.on('disconnect', (reason) => {
  // console.log('Socket disconnected, reason:', reason)
})

export const connectSocket = (token: string, params?: { call_id?: string | number | null, phone_number_id?: string | number | null }) => {
  console.log('Initiating socket connection with auth token and params:', params)
  
  // Disconnect existing connection if any
  if (socket.connected) {
    console.log('Disconnecting existing socket connection')
    socket.disconnect()
  }
  
  socket.io.opts.extraHeaders = {
    Authorization: `Bearer ${token}`
  }
  
  // Add query parameters if provided
  if (params) {
    const query: Record<string, string> = {}
    if (params.call_id) {
      query.call_id = String(params.call_id)
      console.log('Setting call_id in socket query:', query.call_id)
    }
    if (params.phone_number_id) {
      query.phone_number_id = String(params.phone_number_id)
      console.log('Setting phone_number_id in socket query:', query.phone_number_id)
    }
    
    console.log('Setting socket query parameters:', query)
    // Set query parameters for the connection
    socket.io.opts.query = query
  } else {
    console.warn('No params provided for socket connection')
    socket.io.opts.query = {}
  }
  
  console.log('Connecting socket with options:', {
    url: SOCKET_URL,
    extraHeaders: socket.io.opts.extraHeaders ? 'Set' : 'Not set',
    query: socket.io.opts.query
  })
  socket.connect()
}

export const disconnectSocket = () => {
  socket.disconnect()
}

// Add direct connection test utility
export const testConnection = async (): Promise<boolean> => {
  console.log('🔌 [SOCKET] Testing socket connection...');
  
  if (!socket.connected) {
    console.log('🔌 [SOCKET] Socket not connected, attempting to connect');
    socket.connect();
    
    // Wait for connection
    try {
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 5000);
        
        socket.once('connect', () => {
          clearTimeout(timeout);
          resolve();
        });
        
        socket.once('connect_error', (error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });
    } catch (error) {
      console.error('🔌 [SOCKET] Connection failed:', error);
      return false;
    }
  }
  
  // Now test the connection with a round-trip message
  try {
    const connectionTestResult = await new Promise<boolean>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Connection test timeout'));
      }, 5000);
      
      // Send test message
      socket.emit('connection_check', { 
        timestamp: Date.now(),
        message: 'Connection test'
      });
      
      // Wait for response
      socket.once('connection_check_response', (data) => {
        clearTimeout(timeout);
        console.log('🔌 [SOCKET] Received connection check response:', data);
        resolve(true);
      });
    });
    
    console.log('🔌 [SOCKET] Connection test successful');
    return connectionTestResult;
  } catch (error) {
    console.error('🔌 [SOCKET] Connection test failed:', error);
    return false;
  }
};

// Add function to check socket health
export const getSocketHealth = () => {
  const connected = socket.connected;
  const socketId = socket.id;
  
  let transport = 'unknown';
  let readyState = 'unknown';
  let protocol = 'unknown';
  
  try {
    if (socket.io.engine) {
      // Use type assertion for all engine access to make TypeScript happy
      const engine = socket.io.engine as any;
      transport = engine.transport ? engine.transport.name : 'no transport';
      readyState = engine.readyState;
      protocol = engine.protocol ? String(engine.protocol) : 'unknown';
    }
  } catch (error) {
    console.error('🔌 [SOCKET] Error getting engine details:', error);
  }
  
  return {
    connected,
    socketId,
    transport,
    readyState,
    protocol,
    opts: socket.io.opts,
  };
};

// Add function to debug connection issues
export const debugSocketConnection = async () => {
  console.log('🔌 [SOCKET] Starting connection debugging');
  
  // Check current state
  const health = getSocketHealth();
  console.log('🔌 [SOCKET] Current socket health:', health);
  
  // Test URL reachability
  try {
    console.log('🔌 [SOCKET] Testing URL reachability with fetch:', SOCKET_URL);
    const response = await fetch(SOCKET_URL.replace('socket.io', 'api/security/health'));
    console.log('🔌 [SOCKET] URL fetch response:', {
      status: response.status,
      ok: response.ok,
      statusText: response.statusText
    });
  } catch (error) {
    console.error('🔌 [SOCKET] URL fetch failed:', error);
  }
  
  // Force reconnection
  if (socket.connected) {
    console.log('🔌 [SOCKET] Disconnecting for reconnection test');
    socket.disconnect();
  }
  
  console.log('🔌 [SOCKET] Attempting fresh connection');
  socket.io.opts.forceNew = true;
  const connectionResult = await testConnection();
  
  return {
    initialHealth: health,
    connectionTest: connectionResult,
    finalHealth: getSocketHealth()
  };
}; 