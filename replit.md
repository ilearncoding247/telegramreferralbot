# Telegram Referral Bot

## Overview

This is a Python-based Telegram bot that creates and manages referral systems for Telegram channels. The bot allows users to generate unique referral links, tracks successful referrals, and provides a reward system when users reach their referral targets. The system supports multiple channels simultaneously and uses JSON files for data persistence.

## System Architecture

The application follows a modular architecture with clear separation of concerns:

**Core Components:**
- **Bot Handler (`bot_handler.py`)**: Main Telegram bot interface handling user interactions
- **Referral Manager (`referral_manager.py`)**: Business logic for referral system operations
- **Data Manager (`data_manager.py`)**: JSON-based data persistence layer
- **Configuration (`config.py`)**: Centralized configuration management
- **Utilities (`utils.py`)**: Helper functions for encoding/decoding and formatting

**Architecture Pattern**: The system uses a layered architecture where:
1. Bot Handler manages Telegram API interactions
2. Referral Manager handles business logic
3. Data Manager provides persistence abstraction
4. Configuration provides environment-based settings

## Key Components

### Bot Handler
- **Purpose**: Primary interface with Telegram Bot API
- **Responsibilities**: Command handling, message processing, inline keyboards, chat member tracking
- **Key Features**: Admin commands, callback query handling, referral link processing

### Referral Manager
- **Purpose**: Core business logic for referral operations
- **Responsibilities**: Link generation, referral tracking, reward processing
- **Key Features**: Unique code generation, progress tracking, multi-channel support

### Data Manager
- **Purpose**: Data persistence using JSON files
- **Responsibilities**: File operations, data backup, thread-safe access
- **Storage**: Separate JSON files for users, channels, referrals, and pending operations

### Configuration System
- **Purpose**: Environment-based configuration management
- **Features**: Referral targets, reward types, rate limiting, feature flags
- **Flexibility**: Supports admin IDs, notification settings, and behavior customization

## Data Flow

1. **User Onboarding**: User starts bot → Bot checks if referred → Processes referral code if present
2. **Referral Generation**: User joins channel → Bot generates unique referral link → Link stored in data files
3. **Referral Tracking**: New user clicks referral link → Bot tracks join event → Updates referrer's progress
4. **Reward Processing**: User reaches target → Bot enables reward claiming → Admin approval workflow

**Data Storage Pattern**: JSON files with atomic writes and thread-safe operations ensure data consistency.

## External Dependencies

### Required Libraries
- **python-telegram-bot**: Official Telegram Bot API wrapper
- **Standard Library**: json, os, logging, threading, hashlib, base64, uuid

### Telegram Integration
- **Bot API**: Full integration with Telegram Bot API for messaging and administration
- **Channel Management**: Requires bot admin permissions in target channels
- **User Tracking**: Monitors chat member events for join/leave detection

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Bot authentication token from BotFather
- `BOT_USERNAME`: Bot username for referral link generation
- Various configuration options for behavior customization

## Deployment Strategy

### Local Development
- Environment variable setup for bot token and configuration
- JSON file-based storage in local `data/` directory
- Direct Python execution with `python main.py`

### Production Considerations
- **Data Persistence**: JSON files provide simple but reliable storage
- **Backup Strategy**: Configurable backup intervals for data files
- **Logging**: Comprehensive logging with configurable levels
- **Error Handling**: Graceful error handling for network and API issues

### Scalability Notes
- Current architecture supports moderate usage with JSON storage
- Thread-safe operations ensure concurrent request handling
- Rate limiting prevents abuse and API quota issues

## Changelog

- June 28, 2025. Initial setup
- June 29, 2025. Bot successfully deployed and running in production mode for subscriber use

## User Preferences

Preferred communication style: Simple, everyday language.