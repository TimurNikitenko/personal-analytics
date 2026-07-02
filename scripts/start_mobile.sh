#!/bin/bash
# start_mobile.sh - Automatically detect LAN IP and run Expo Packager for Expo Go.

# Resolve root directory of personal-analytics
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$DIR")"

# Check if tunnel mode is requested
if [ "$1" == "--tunnel" ]; then
    echo "🌐 Starting Expo Packager in Tunnel Mode (ngrok)..."
    echo "💡 This works even with active VPNs or on different Wi-Fi networks."
    cd "$PROJECT_ROOT/mobile_app"
    npx expo start --tunnel
else
    # Detect the host's primary LAN IP (ignores common docker/local subnets)
    LAN_IP=$(hostname -I | tr ' ' '\n' | grep -v '^172\.\(17\|18\|19\)\.' | grep -v '^127\.' | head -n 1)

    if [ -z "$LAN_IP" ]; then
        echo "⚠️ Warning: Could not detect primary LAN IP. Defaulting to 127.0.0.1"
        LAN_IP="127.0.0.1"
    else
        echo "❇️ Detected LAN IP: $LAN_IP"
    fi

    echo "🔗 Expo Go Metro URL: exp://$LAN_IP:8081"
    echo "🚀 Starting Metro Bundler..."

    # Run from mobile_app directory
    cd "$PROJECT_ROOT/mobile_app"
    REACT_NATIVE_PACKAGER_HOSTNAME="$LAN_IP" npx expo start --go
fi
