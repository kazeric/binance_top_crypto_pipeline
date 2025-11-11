# Binance Top Crypto Pipeline

A comprehensive real-time data pipeline that captures, processes, and visualizes cryptocurrency market data from Binance. This project leverages Apache Kafka, PostgreSQL, Cassandra, and Grafana to build a scalable, event-driven architecture for financial data processing.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [System Components](#system-components)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Running the Pipeline](#running-the-pipeline)
- [Data Flow](#data-flow)
- [Configuration](#configuration)
- [Monitoring & Visualization](#monitoring--visualization)
- [Kafka Connect Connectors](#kafka-connect-connectors)
- [Troubleshooting](#troubleshooting)

## Project Overview

This project implements a real-time cryptocurrency market data pipeline that:

- **Extracts** live market data from Binance API (kline data, recent trades, order book, 24hr statistics)
- **Transforms** data using PostgreSQL with Debezium for change data capture (CDC)
- **Streams** events through Apache Kafka for decoupled processing
- **Persists** data to Apache Cassandra for time-series analytics
- **Visualizes** metrics and trends through Grafana dashboards

**Use Cases:**

- Real-time market analysis and price tracking
- Technical analysis signal generation
- Market trend detection
- Risk monitoring and alerting
- Historical data analytics

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Binance API                                   │
│              (kline, recent_trades, order_book)                 │
└────────────────────┬────────────────────────────────────────────┘
                     │ (ETL Producer)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                            │
│  (cap_stock_db: kline_data, order_book, recent_trades, top_24hr)│
└────────────────────┬────────────────────────────────────────────┘
                     │ (Debezium CDC)
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Apache Kafka                                   │
│    Topics: cap_stock.public.* (kline_data, trades, order_book) │
└──────────┬──────────────────────────────────────────────────────┘
           │
     ┌─────┴──────┐
     │            │
     ▼            ▼
┌──────────────┐ ┌──────────────────────┐
│  Cassandra   │ │  Kafka Connect UI    │
│  (Analytics) │ │  (Monitoring)        │
└──────────────┘ └──────────────────────┘
     │
     ▼
┌──────────────────────────────────────────┐
│        Grafana Dashboards                │
│   (Real-time visualization & metrics)    │
└──────────────────────────────────────────┘
```

---

## System Components

### 1. **Binance ETL Producer**

- **Service:** `etl`
- **Language:** Python
- **Purpose:** Fetches live market data from Binance API and writes to PostgreSQL
- **Data Collected:**
  - **Kline Data:** OHLCV (Open, High, Low, Close, Volume) candlestick data
  - **Recent Trades:** Individual trade transactions
  - **Order Book:** Current bid/ask levels
  - **24hr Statistics:** Price change, volume, price extremes
- **Location:** `./producer/`

### 2. **PostgreSQL Database**

- **Image:** `debezium/postgres:15`
- **Container:** `postgres`
- **Port:** `5432`
- **Database:** `cap_stock_db`
- **User:** `dbz` / Password: `dbz`
- **Features:**
  - WAL (Write-Ahead Logging) enabled for CDC
  - Logical replication support
  - Tables: `kline_data`, `order_book`, `recent_trades`, `top_24hr`
- **Purpose:** Primary OLTP database for incoming market data

### 3. **Apache Zookeeper**

- **Image:** `quay.io/debezium/zookeeper:3.1`
- **Container:** `zookeeper`
- **Port:** `2181`
- **Purpose:** Manages Kafka cluster coordination and broker state

### 4. **Apache Kafka**

- **Image:** `quay.io/debezium/kafka:3.1`
- **Container:** `kafka`
- **Ports:**
  - Internal: `9092` (container-to-container)
  - External: `29092` (localhost access)
- **Topics:**
  - `cap_stock.public.kline_data` - Candlestick data events
  - `cap_stock.public.recent_trades` - Trade events
  - `cap_stock.public.order_book` - Order book updates
  - `cap_stock.public.top_24hr` - 24-hour statistics
- **Purpose:** Event streaming backbone; decouples data producers from consumers

### 5. **Kafka Connect**

- **Image:** `quay.io/debezium/connect:3.1`
- **Container:** `connect`
- **Port:** `8083`
- **Connectors:**
  - **Debezium PostgreSQL Connector:** Captures changes from PostgreSQL and publishes to Kafka
  - **Cassandra Sink Connector:** Consumes Kafka events and writes to Cassandra
- **Purpose:** Manages data pipeline orchestration between databases and Kafka

### 6. **Apache Cassandra**

- **Image:** `cassandra:4.0.19`
- **Container:** `cassandra`
- **Port:** `9042`
- **Cluster:** `MyCassandraCluster` (Datacenter1)
- **User:** `admin` / Password: `admin`
- **Purpose:** Distributed time-series database for analytical queries and historical data
- **Health Check:** Verifies cluster status via `nodetool`

### 7. **Grafana**

- **Image:** `grafana/grafana:main-ubuntu`
- **Container:** `grafana`
- **Port:** `3001` → `3000` (internal)
- **Default Credentials:** `admin` / `admin`
- **Purpose:** Real-time dashboards and visualization of market metrics
- **Data Source:** PostgreSQL and Cassandra

### 8. **AKHQ (Kafka UI)**

- **Image:** `tchiotludo/akhq:latest`
- **Container:** `akhq`
- **Port:** `8080`
- **Purpose:** Web-based Kafka cluster management and monitoring
- **Features:** Topic browsing, message inspection, Kafka Connect management

---

## Prerequisites

- **Docker Desktop** (or Docker + Docker Compose)
- **Python 3.9+** (if running ETL locally)
- **curl** (for registering connectors)
- **Git**
- Binance API access (free tier available)

## Setup & Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd binance_top_crypto_pipeline
```

### Step 2: Create Environment File

Create `./producer/.env` with your Binance API credentials:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
DATABASE_URL=postgresql://dbz:dbz@postgres:5432/cap_stock_db
```

### Step 3: Start Docker Containers

```bash
docker-compose up -d
```

This will start all services in the following order:

1. PostgreSQL (with health check)
2. Zookeeper
3. Kafka
4. Cassandra (with health check)
5. Kafka Connect
6. ETL Producer (depends on Postgres & Cassandra)
7. Grafana
8. AKHQ

### Step 4: Verify Services

```bash
docker-compose ps
```

Expected output: All services should show status `Up`.

### Step 5: Register Kafka Connectors

Once Kafka Connect is running, register the connectors:

```bash
chmod +x connect_connectors.sh
./connect_connectors.sh
```

This script:

- Posts `register-postgres.json` → Registers Debezium PostgreSQL connector
- Posts `register_cassandra.json` → Registers Cassandra sink connector

Verify registration:

```bash
curl http://localhost:8083/connectors
```

---

## Running the Pipeline

### Start the Full Pipeline

```bash
docker-compose up -d
```

### Access Web endpoints

| Service       | URL                   | Credentials   |
| ------------- | --------------------- | ------------- |
| Grafana       | http://localhost:3001 | admin / admin |
| AKHQ (Kafka)  | http://localhost:8080 | -             |
| Kafka Connect | http://localhost:8083 | -             |
| PostgreSQL    | localhost:5432        | dbz / dbz     |
| Cassandra     | localhost:9042        | admin / admin |

---

## Data Flow

### 1. **Data Extraction (Producer)**

```
Binance API
  ↓
ETL Service (Python)
  ↓
PostgreSQL Tables:
  - kline_data (candlestick data)
  - recent_trades (trade records)
  - order_book (current market depth)
  - top_24hr (24-hour statistics)
```

### 2. **Change Data Capture (CDC)**

```
PostgreSQL (Logical Replication)
  ↓
Debezium PostgreSQL Connector (Kafka Connect)
  ↓
Kafka Topics (cap_stock.public.*):
  - cap_stock.public.kline_data
  - cap_stock.public.recent_trades
  - cap_stock.public.order_book
  - cap_stock.public.top_24hr
```

### 3. **Event Consumption & Analytics**

```
Kafka Topics
  ↓
Cassandra Sink Connector (Kafka Connect)
  ↓
Cassandra Tables:
  - cap_stock.kline_data
  - cap_stock.recent_trades
  - cap_stock.order_book
  - cap_stock.top_24hr
  ↓
Grafana Queries & Dashboards
```

### 4. **Visualization**

```
PostgreSQL / Cassandra
  ↓
Grafana Data Sources
  ↓
Real-time Dashboards & Alerts
```

---

## Kafka Connect Connectors

### Debezium PostgreSQL Connector

**File:** `register-postgres.json`

**Behavior:**

- Monitors PostgreSQL for INSERT/UPDATE/DELETE on specified tables
- Publishes before and after values to Kafka topics
- Maintains replication slot for crash recovery

### Cassandra Sink Connector

**File:** `register_cassandra.json`

**Behavior:**

- Consumes Kafka topics in real-time
- Maps event fields to Cassandra table columns
- Uses Debezium unwrap transformer to extract record state
- Writes events to Cassandra with minimal latency

---

## Monitoring & Visualization

### Grafana Setup

1. **Access Grafana:** http://localhost:3001
2. **Add Data Sources:**
   - PostgreSQL: `postgres:5432` (cap_stock_db)
   - Cassandra: `cassandra:9042`
3. **Create Dashboards:**
   - Real-time price charts (kline data)
   - Trade volume and frequency
   - Order book heatmaps
   - 24hr price change metrics
   - Market volatility indicators
4. **Add Variables:**
   - symbols that will be used in the to create the filter to switch between crypto symbols

## Configuration

### Cassandra Configuration

```yaml
CASSANDRA_CLUSTER_NAME: MyCassandraCluster
CASSANDRA_DC: datacenter1
```

- Single-node cluster (production would use multi-node setup)
- Persistent volume: `cassandra_data:/var/lib/cassandra`

---

## Project Structure

```
binance_top_crypto_pipeline/
├── docker-compose.yml              # Service orchestration
├── connect_connectors.sh            # Connector registration script
├── register-postgres.json           # Debezium PostgreSQL config
├── register_cassandra.json          # Cassandra sink config
├── register_cassandra_test.json     # Cassandra test config
├── producer/                        # ETL Service
│   ├── main.py                     # Main ETL script
│   ├── cassandra_setup.py          # Cassandra initialization
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # ETL container image
│   └── .env                        # Environment variables
├── plugins/                         # Kafka Connect plugins
│   └── kafka-connect-cassandra-sink-1.7.3/
├── dashboard/                       # Grafana dashboards
├── grafana_data/                    # Grafana persistent data
└── README.md                        # This file
```

---

## 🚫 Stopping & Cleanup

### Stop All Services

```bash
docker-compose down
```

### Stop and Remove Volumes (CAUTION: Deletes data)

```bash
docker-compose down -v
```

### Remove Specific Service

```bash
docker-compose stop <service_name>
docker-compose rm <service_name>
```
