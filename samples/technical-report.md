# System Architecture & Performance Analysis:  
## Cloud-Native Data Pipeline for Real-Time Financial Risk Analytics

---

**Document Control**

| Field | Value |
|---|---|
| Document ID | TECH-REP-2026-001 |
| Version | 2.1 |
| Classification | CONFIDENTIAL — INTERNAL USE ONLY |
| Author | Engineering Team, Upstride Labs Limited |
| Date | 26 June 2026 |
| Reviewers | CTO, Head of Platform, Security Lead |

---

## Executive Summary

This technical report presents the architecture, implementation, and performance characteristics of a cloud-native data pipeline designed for real-time financial risk analytics. The system processes approximately 2.8 million market data events per second, evaluates 147 risk metrics across 22,000 positions with sub-100-millisecond latency, and achieves 99.995% uptime across a six-month observation window.

The pipeline is built on a stack comprising Apache Kafka for ingestion, Apache Flink for stream processing, a custom risk engine written in Rust, and a time-series database layer backed by ClickHouse. Deployment is managed via Kubernetes on AWS EKS, with infrastructure defined as code using Terraform.

Key findings include: (a) a 12.4× throughput improvement over the previous Java-based engine; (b) a 73% reduction in infrastructure cost per million events processed; and (c) the identification of three previously undetected classes of latency anomaly through the implementation of a novel statistical monitoring framework.

---

## 1. Introduction

### 1.1 Background

Financial institutions operating in global markets face increasingly stringent regulatory requirements for real-time risk monitoring. The Basel Committee's Fundamental Review of the Trading Book (FRTB) and the European Securities and Markets Authority's (ESMA) MiFID II/MiFIR framework mandate that firms compute and report risk metrics — including Value-at-Risk (VaR), Expected Shortfall (ES), and various sensitivity measures — on an intraday basis, with some metrics requiring near-real-time availability to trading desks [1,2].

Traditional risk systems, typically built on end-of-day batch processing architectures, are ill-suited to these demands. A 2025 industry survey by Celent found that 67% of Tier 1 and Tier 2 banks considered their existing risk infrastructure "inadequate for real-time regulatory requirements", and 82% had active programmes to modernise their risk technology stacks [3].

### 1.2 Problem Statement

The legacy risk analytics platform at the study institution exhibited three fundamental limitations:

1. **Throughput ceiling:** The Java-based risk engine, built on a conventional service-oriented architecture with synchronous REST communication, plateaued at approximately 225,000 events per second against a peak market data rate of 2.8 million events per second.

2. **Latency variability:** End-to-end latency — measured from market data tick arrival to risk metric availability — exhibited a bimodal distribution with a long tail. While the median latency was 780 ms, the 99th percentile exceeded 4.2 seconds, rendering the system unsuitable for intraday risk limit monitoring.

3. **Operational fragility:** The system lacked automated failover, graceful degradation, and comprehensive observability. Production incidents averaged 14 per month, with a mean time to resolution (MTTR) of 94 minutes.

### 1.3 Objectives

The Cloud-Native Risk Pipeline (CNRP) project was initiated with the following objectives:

- Achieve sustained throughput of 3 million events per second with sub-100 ms end-to-end latency at the 99th percentile;
- Reduce infrastructure cost per million events by at least 50%;
- Achieve 99.99% availability with automated failover and self-healing;
- Provide comprehensive, real-time observability of pipeline health and risk metric accuracy; and
- Maintain full backward compatibility with downstream consumers of risk data.

### 1.4 Scope

This report covers the architectural design (Section 2), detailed component analysis (Section 3), performance benchmarking methodology and results (Section 4), operational characteristics (Section 5), and lessons learned (Section 6). Security architecture and compliance mapping are addressed in a companion document [4].

---

## 2. Architectural Design

### 2.1 Design Principles

The architecture was guided by six principles:

| Principle | Description | Architectural Consequence |
|---|---|---|
| **Back-pressure everywhere** | Every component must signal its capacity to upstream producers | Reactive streams with non-blocking I/O throughout |
| **Crash-only design** | Components must survive unexpected termination and restart cleanly | Idempotent processing, append-only logs, stateless compute where possible |
| **Observability as a first-class concern** | Every component must emit metrics, traces, and structured logs | OpenTelemetry instrumentation embedded in every service |
| **Mechanical sympathy** | Exploit hardware characteristics (CPU cache lines, SIMD, memory hierarchy) | Rust for the risk engine core; columnar data layouts |
| **Infrastructure as data** | All infrastructure defined declaratively; no manual intervention | Terraform modules; GitOps via FluxCD |
| **Defence in depth** | Security at every layer, not just the perimeter | mTLS, SPIFFE identities, network policies, data encryption at rest and in transit |

### 2.2 High-Level Architecture

The CNRP comprises five logical layers, each scaling independently:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       CONSUMER LAYER                                 │
│  Risk Dashboards │ Trading Systems │ Regulatory Reporting │ APIs     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      SERVING LAYER                                   │
│  GraphQL Gateway (Rust) │ REST API (Go) │ gRPC Streaming (Rust)      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      STORAGE LAYER                                   │
│  ClickHouse (hot) │ S3/Parquet (warm) │ Glacier (cold) │ Redis Cache │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      COMPUTE LAYER                                   │
│  Risk Engine (Rust) │ Flink CEP │ Materialised Views (ClickHouse)    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      INGESTION LAYER                                 │
│  Kafka Cluster (12 brokers) │ Schema Registry │ Dead Letter Queue    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Technology Stack

The component-level technology stack is detailed below:

```yaml
infrastructure:
  cloud_provider: "AWS"
  region: "eu-west-1"
  kubernetes: "EKS 1.28"
  service_mesh: "Istio 1.19"
  
ingestion:
  platform: "Apache Kafka 3.6"
  brokers: 12
  topics: 48
  partitions_per_topic: 24
  retention: "7 days"
  schema_registry: "Confluent 7.5"

compute:
  stream_processing: "Apache Flink 1.18"
  risk_engine: "Rust 1.75 + SIMD"
  materialized_views: "ClickHouse SQL"

storage:
  time_series: "ClickHouse 23.11"
  object_store: "AWS S3 (Standard)"
  cache: "Redis 7.2 (Cluster mode)"
  
observability:
  metrics: "Prometheus + Thanos"
  tracing: "OpenTelemetry → Jaeger"
  logging: "Vector → Loki"
  dashboards: "Grafana 10"
```

---

## 3. Component Analysis

### 3.1 Ingestion Layer

#### 3.1.1 Kafka Configuration

The Kafka cluster is provisioned across three availability zones (`eu-west-1a`, `eu-west-1b`, `eu-west-1c`), with four brokers per zone. Each broker runs on an `r6i.4xlarge` instance (16 vCPU, 128 GiB RAM, 2 × 1.9 TB NVMe SSD). The aggregate cluster capacity is 48 vCPU, 384 GiB RAM, and 45.6 TB of raw NVMe storage.

Topic design follows a domain-driven partitioning strategy:

| Domain | Topic Prefix | Partition Count | Avg. Message Size | Peak Throughput (msg/s) |
|---|---|---|---|---|
| Equity Spot | `eq.spot` | 24 | 1.2 KiB | 1,400,000 |
| Equity Derivatives | `eq.deriv` | 24 | 3.8 KiB | 620,000 |
| Fixed Income | `fi` | 24 | 2.1 KiB | 310,000 |
| FX Spot | `fx.spot` | 24 | 0.9 KiB | 890,000 |
| FX Derivatives | `fx.deriv` | 24 | 4.2 KiB | 180,000 |
| Commodities | `cmdty` | 24 | 1.8 KiB | 130,000 |
| Credit | `credit` | 24 | 5.6 KiB | 45,000 |

#### 3.1.2 Schema Management

All messages are serialised using Apache Avro with a Confluent Schema Registry enforcing compatibility. The schema evolution strategy is `BACKWARD` for all topics, ensuring that consumers running older schema versions can read messages produced by newer producers. Over the six-month observation window, 17 schema changes were deployed, all using the `BACKWARD` compatibility mode, with zero consumer-side deserialisation failures.

### 3.2 Compute Layer

#### 3.2.1 Flink Stream Processing

Apache Flink jobs are deployed in session mode on a dedicated Flink Kubernetes Operator. The primary Flink job — the Market Data Normaliser — consumes from all seven Kafka topic domains, normalises timestamps to UTC with microsecond precision, enriches messages with instrument reference data from a Redis cache, and publishes to a unified `risk.input` topic.

The Flink job is configured with:

```python
flink_config = {
    "parallelism.default": 48,
    "taskmanager.numberOfTaskSlots": 8,
    "taskmanager.memory.process.size": "16g",
    "state.backend": "rocksdb",
    "state.checkpoints.dir": "s3://cnrp-flink-checkpoints",
    "execution.checkpointing.interval": "5000ms",
    "execution.checkpointing.min-pause": "2000ms",
    "execution.checkpointing.timeout": "10min",
}
```

Checkpoint duration averages 1.8 seconds (P99: 3.2 seconds), well within the 10-minute timeout, with zero checkpoint failures across the observation window.

#### 3.2.2 Risk Engine (Rust)

The risk engine is the core computational component, and its design warrants detailed examination. Written in Rust for its combination of zero-cost abstractions, memory safety without garbage collection, and excellent SIMD support, the engine evaluates 147 risk metrics across 22,000 positions on every market data event.

**Data Structures:**

The engine uses a Struct-of-Arrays (SoA) layout for position data, optimised for cache-line utilisation on modern x86-64 processors:

```rust
#[repr(C)]
struct PositionBook {
    // Each field is a Vec<T> stored contiguously in memory
    instrument_ids: Vec<u64>,
    quantities: Vec<f64>,
    cost_bases: Vec<f64>,
    // ... 18 more fields
}

impl PositionBook {
    fn evaluate_risk_metrics(&self, market_data: &MarketDataSnapshot) -> RiskMetrics {
        // SIMD-accelerated: processes 4 positions per CPU instruction on AVX2
        #[cfg(target_feature = "avx2")]
        {
            self.evaluate_simd_avx2(market_data)
        }
        #[cfg(not(target_feature = "avx2"))]
        {
            self.evaluate_scalar(market_data)
        }
    }
}
```

**Performance Characteristics:**

The Rust engine processes a full portfolio revaluation (22,000 positions × 147 metrics) in 47 microseconds on a `c6i.8xlarge` instance. This represents a 12.4× improvement over the legacy Java engine (583 microseconds on equivalent hardware) and a 23.7× improvement over the Python prototype (1,114 microseconds).

| Engine | Portfolio Reval (μs) | Throughput (events/s) | Memory (GiB) | CPU Utilisation |
|---|---|---|---|---|
| Python (prototype) | 1,114 | 18,000 | 8.2 | 100% |
| Java (legacy) | 583 | 225,000 | 4.8 | 89% |
| Rust (CNRP) | **47** | **2,800,000** | **1.1** | **62%** |

### 3.3 Storage Layer

#### 3.3.1 ClickHouse Configuration

ClickHouse is deployed as a 9-node cluster (3 shards × 3 replicas) on `c6i.4xlarge` instances with 2 × 1.9 TB NVMe SSD each. The cluster stores 90 days of hot data, after which data is compacted into Parquet files and moved to S3 for warm storage (90 days to 7 years).

Table schema for the primary `risk_metrics` table:

```sql
CREATE TABLE risk_metrics (
    timestamp DateTime64(6) CODEC(DoubleDelta, ZSTD),
    instrument_id UInt64,
    metric_type LowCardinality(String),
    metric_value Float64 CODEC(Gorilla, ZSTD),
    book_id UInt32,
    source_topic LowCardinality(String),
    ingest_latency_us UInt32,
    compute_latency_us UInt32,
    tags Array(String)
) ENGINE = ReplicatedMergeTree
PARTITION BY toStartOfHour(timestamp)
ORDER BY (instrument_id, metric_type, timestamp)
SETTINGS index_granularity = 8192;
```

#### 3.3.2 Query Performance

The following table presents query latency benchmarks for common access patterns:

| Query Pattern | Cold Cache (ms) | Warm Cache (ms) | P99 (ms) |
|---|---|---|---|
| Single instrument, 1 metric, 1 hour | 12 | 0.8 | 18 |
| Single instrument, all metrics, 1 day | 47 | 3.2 | 68 |
| Portfolio VaR, 22,000 instruments, latest | 230 | 18 | 410 |
| Portfolio ES, all instruments, 1 day history | 890 | 72 | 1,340 |
| Cross-sectional risk decomposition | 1,450 | 140 | 2,100 |
| Regulatory report (FRTB SA) | 3,200 | 340 | 5,600 |

---

## 4. Performance Benchmarking

### 4.1 Methodology

Performance benchmarks were conducted using a synthetic market data generator calibrated against historical data from Q1 2025. The generator replays 24 hours of market data at configurable acceleration factors (1×, 5×, 10×, and 20× real-time), capturing both normal trading conditions and stress events. The following benchmarks were measured at each acceleration factor:

- **End-to-end latency:** The interval between a market data event entering the first Kafka topic and the corresponding risk metric becoming queryable in ClickHouse, measured at the 50th, 95th, 99th, and 99.9th percentiles.
- **Throughput:** The sustained rate of market data events processed per second, measured at the Kafka consumer group level.
- **Correctness:** The absolute deviation of CNRP-computed risk metrics from a reference implementation (a brute-force calculation performed by an independent risk analytics library), measured as a percentage error.
- **Resource utilisation:** CPU, memory, network I/O, and disk I/O across all CNRP components.

### 4.2 Results

#### 4.2.1 Latency

| Acceleration Factor | P50 (ms) | P95 (ms) | P99 (ms) | P99.9 (ms) |
|---|---|---|---|---|
| 1× (baseline) | 32 | 58 | 78 | 112 |
| 5× | 34 | 61 | 82 | 124 |
| 10× | 37 | 67 | 91 | 148 |
| 20× | 44 | 81 | 114 | 203 |

At 20× acceleration — equivalent to a peak event rate of 56 million events per second, or 20 times the design target — the pipeline maintains a P99 latency of 114 ms, with the P99.9 tail at 203 ms. The principal contributor to tail latency at extreme acceleration factors is ClickHouse merge tree partition compaction, which contends for NVMe I/O bandwidth.

#### 4.2.2 Throughput

The pipeline achieves maximum sustained throughput of 4.7 million events per second before back-pressure from the Kafka consumer group triggers Flink's adaptive scaling mechanism. This represents a 1.68× safety margin above the 2.8 million events per second design target.

#### 4.2.3 Correctness

Across all acceleration factors and all 147 risk metrics, the maximum observed absolute percentage deviation from the reference implementation was 0.00034%. The mean deviation was 0.00007%. These deviations are attributable to floating-point rounding differences between the Rust engine's SIMD code path and the scalar reference implementation.

---

## 5. Operational Characteristics

### 5.1 Availability

The CNRP achieved 99.995% availability (26.3 minutes of downtime) over the six-month observation window (1 January – 30 June 2026). The following table disaggregates the downtime by root cause:

| Incident | Duration (minutes) | Root Cause | Mitigation |
|---|---|---|---|
| AWS EKS control plane degradation | 11.2 | AWS regional issue (eu-west-1) | Multi-AZ deployment; workloads unaffected but API server unavailable for scaling operations |
| ClickHouse replication lag cascade | 7.8 | Network partition between AZs `a` and `b` | Automated replica promotion; partition healed within 3 minutes |
| Flink checkpoint timeout → job restart | 4.3 | S3 throttling during mass log upload | Increased S3 request rate limits; implemented checkpoint write throttling |
| Kafka broker disk failure | 3.0 | NVMe hardware failure on broker 7 | Automated partition reassignment; Kafka's rack-aware replication prevented data loss |

### 5.2 Observability

The observability stack processes approximately 2.1 TB of telemetry data per day:

| Signal Type | Daily Volume | Retention | Storage Backend |
|---|---|---|---|
| Metrics (Prometheus) | 6.8 million samples | 90 days | Thanos (S3) |
| Traces (OpenTelemetry) | 420 million spans | 30 days | Jaeger (Cassandra) |
| Logs (Structured JSON) | 1.8 TB raw | 14 days | Loki (S3) |

The team defined 47 Service Level Indicators (SLIs), each with a corresponding Service Level Objective (SLO) and burn-rate-based alerting policy. Over the observation window, 14 SLOs were breached on at least one occasion, triggering a total of 23 alerts. Of these, 18 were resolved within the defined error budget window; 5 required a formal incident response.

---

## 6. Lessons Learned and Future Work

### 6.1 What Worked Well

1. **Rust for performance-critical paths:** The decision to implement the risk engine in Rust was validated by the 12.4× throughput improvement and the elimination of garbage-collection-related latency spikes. The learning curve was steep (approximately 3 months for the team to achieve productivity), but the investment was recovered through reduced operational overhead and eliminated classes of runtime errors.

2. **Schema-first design:** Enforcing Avro schema compatibility through the Confluent Schema Registry eliminated an entire category of production incidents that had plagued the legacy system (schema mismatch leading to consumer crashes).

3. **GitOps deployment:** FluxCD's automated drift detection and reconciliation reduced deployment-related incidents from an average of 6 per month in the legacy system to zero in the CNRP.

### 6.2 What We Would Do Differently

1. **Earlier investment in load testing:** The first production-scale test (at 10× acceleration) revealed a subtle interaction between Flink's checkpointing mechanism and S3's request rate limits that required a week of intensive debugging. Earlier investment in chaos engineering and load testing would have surfaced this issue in pre-production.

2. **ClickHouse schema design:** The initial `ORDER BY` key for the `risk_metrics` table was `(timestamp, instrument_id)`, optimised for time-range queries. However, the dominant query pattern turned out to be instrument-centric (single instrument, multiple metrics, over a time range). Changing the `ORDER BY` to `(instrument_id, metric_type, timestamp)` improved P50 query latency by 6.7×, but required a 3-day table rewrite.

### 6.3 Future Work

1. **GPU acceleration:** The risk metric evaluation is an embarrassingly parallel computation. Preliminary benchmarks using CUDA on an NVIDIA A100 GPU suggest a potential 8–12× further throughput improvement for the risk engine core.

2. **Multi-cloud deployment:** While the CNRP's Terraform modules are cloud-agnostic in principle, significant work remains to achieve a true multi-cloud deployment spanning AWS and GCP for resilience against single-provider failure.

3. **Real-time model calibration:** Currently, risk models are calibrated daily using a batch process. An experimental online calibration system using stochastic gradient descent on streaming data has shown promising initial results and is scheduled for production evaluation in Q4 2026.

---

## Appendices

### Appendix A: SLO Definitions

| SLI | SLO Target | Measurement Window | Error Budget (monthly) |
|---|---|---|---|
| End-to-end latency P99 | < 100 ms | 30 days | 43.8 minutes |
| Kafka consumer lag | < 5,000 messages | 15 minutes | 5 minutes |
| Flink checkpoint success rate | > 99.9% | 24 hours | 1.44 minutes |
| ClickHouse query availability | > 99.99% | 30 days | 4.38 minutes |
| API gateway error rate (5xx) | < 0.1% | 30 days | 0.1 hours |

### Appendix B: Infrastructure Cost Breakdown

| Component | Monthly Cost (USD) | % of Total |
|---|---|---|
| EC2 (EKS worker nodes) | $38,400 | 38.4% |
| Kafka (MSK equivalent, self-managed) | $16,200 | 16.2% |
| ClickHouse (EC2 + NVMe) | $14,800 | 14.8% |
| S3 (checkpoints + warm storage) | $8,600 | 8.6% |
| Networking (data transfer) | $7,200 | 7.2% |
| Observability (Thanos, Loki, Jaeger) | $7,800 | 7.8% |
| Other (ELB, NAT Gateway, KMS, etc.) | $7,000 | 7.0% |
| **Total** | **$100,000** | **100%** |

### Appendix C: References

1. Basel Committee on Banking Supervision, "Minimum Capital Requirements for Market Risk," BIS, January 2019.

2. European Securities and Markets Authority, "MiFID II/MiFIR Review Report," ESMA, 2024.

3. Celent, "Risk Technology in Capital Markets: 2025 Survey," Celent Research, 2025.

4. Upstride Labs, "CNRP Security Architecture and Compliance Mapping," Internal Document, 2026.

5. Kreps, J., Narkhede, N., & Rao, J., "Kafka: A Distributed Messaging System for Log Processing," NetDB, 2011.

6. Carbone, P., et al., "Apache Flink: Stream and Batch Processing in a Single Engine," IEEE Data Engineering Bulletin, 2015.

7. ClickHouse, Inc., "ClickHouse Documentation: MergeTree Engine," 2024.

---

**END OF REPORT**
